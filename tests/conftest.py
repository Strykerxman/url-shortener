import pytest
import pytest_asyncio
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from starlette.datastructures import URL

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

from app.main import app


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_file_encoding="utf-8", extra="ignore"
    )
    database_url: str
    base_url: str = "http://testserver"
    debug: bool = True
    env_name: str = "test"

    @computed_field(return_type=str)
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        else:
            raise ValueError("DATABASE_URL is required")


@pytest_asyncio.fixture(scope="function")
async def api_client(test_settings):
    async with AsyncClient(
        base_url=test_settings.base_url, transport=ASGITransport(app=app)
    ) as client:
        yield client


@pytest.fixture(scope="session")
def test_settings():
    return TestSettings()


@pytest.fixture(autouse=True, scope="function")
def override_get_settings(test_settings):
    from app.core.config import get_settings

    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture(autouse=True, scope="function")
def override_get_admin_info(test_settings):
    from app.core import url_utils

    def _mock_get_admin_info(db_url):
        base_url = URL(test_settings.base_url)
        db_url.url = str(base_url.replace(path=db_url.key))
        db_url.admin_url = str(base_url.replace(path=f"admin/{db_url.secret_key}"))

        return db_url

    app.dependency_overrides[url_utils.get_admin_info] = _mock_get_admin_info
    yield _mock_get_admin_info
    app.dependency_overrides.pop(url_utils.get_admin_info, None)


@pytest.fixture(scope="function")
def fake_redis():
    """Real in-memory Redis implementation via fakeredis — no mocks."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True, scope="function")
def override_get_redis(fake_redis):
    from app.database import get_redis

    async def _get_fake_redis():
        return fake_redis

    app.dependency_overrides[get_redis] = _get_fake_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture(scope="session")
def setup_test_db(test_settings):
    settings = test_settings
    engine = create_engine(settings.sqlalchemy_database_url, future=True)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url)

    # Use the connection injection pattern to ensure migrations hit the test DB
    with engine.begin() as conn:
        alembic_cfg.attributes["connection"] = conn
        command.upgrade(alembic_cfg, "head")

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(setup_test_db):
    from app.database import get_db

    connection = setup_test_db.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = Session()

    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)
