from collections import defaultdict
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_file_encoding="utf-8", extra="ignore"
    )
    database_url: str = Field(..., env="DATABASE_URL")
    base_url: str
    debug: bool = True
    env_name: str = "test"


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
def session_clear_settings_cache():
    """
    Clears cached settings after each test to prevent config leakage.
    """
    yield
    from app.core.config import get_settings
    get_settings.cache_clear()


@pytest.fixture(scope="function")
def extract_bearer_token():
    """
    Helper to extract the Bearer token from an admin_url response value.
    
    Since admin_url now contains: "Use Authorization header: Bearer <token>",
    this extracts just the token part.
    """
    
    def _extract(admin_url_str: str) -> str:
        # Format: "Use Authorization header: Bearer <secret_key>"
        if "Bearer " not in admin_url_str:
            raise ValueError(f"Could not extract Bearer token from: {admin_url_str}")
        return admin_url_str.split("Bearer ")[1]
    return _extract


@pytest.fixture(scope="function")
def bearer_token_header(extract_bearer_token):
    """Helper to create a complete Authorization header dict for API requests."""

    def _create_header(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _create_header


@pytest.fixture(scope="function")
def mocked_redis():
    storage = defaultdict(lambda: None)
    mock_redis = AsyncMock(spec=Redis)

    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()

    mock_redis.get.side_effect = lambda key: storage.get(key)
    mock_redis.set.side_effect = (
        lambda key, val, ex=3600 * 24: storage.update({key: val}) or True
    )
    mock_redis.delete.side_effect = lambda key: storage.pop(key, None) is not None

    mock_redis.ping = AsyncMock()
    yield mock_redis
    storage.clear()


@pytest.fixture(autouse=True, scope="function")
def mock_get_redis(mocked_redis):
    from app.database import get_redis

    async def _get_mock_redis():
        yield mocked_redis

    app.dependency_overrides[get_redis] = _get_mock_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture(scope="session")
def setup_test_db(test_settings):
    from app.database import database as database_module

    settings = test_settings

    # Force test process to use test database globals, independent of local env files.
    engine = create_engine(settings.database_url, echo=settings.debug)
    database_module.engine = engine
    database_module.SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    # Use the connection injection pattern to ensure migrations hit the test DB
    with engine.begin() as conn:
        alembic_cfg.attributes["connection"] = conn
        command.upgrade(alembic_cfg, "head")

    yield engine

    engine.dispose()
    database_module.engine = None
    database_module.SessionLocal = None


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
    if transaction.is_active:
        transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)
