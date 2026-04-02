from collections import defaultdict
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import Field, computed_field
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


@pytest.fixture(scope="function")
def extract_bearer_token():
    """
    Helper to extract the Bearer token from an admin_url response value.
    
    Since admin_url now contains: "Use Authorization header: Bearer <token>",
    this extracts just the token part.
    
    Example:
        response = await api_client.post("/url", ...)
        token = extract_bearer_token(response.json()["admin_url"])
        headers = {"Authorization": f"Bearer {token}"}
    """
    def _extract(admin_url_str: str) -> str:
        # Format: "Use Authorization header: Bearer <secret_key>"
        if "Bearer " not in admin_url_str:
            raise ValueError(f"Could not extract Bearer token from: {admin_url_str}")
        return admin_url_str.split("Bearer ")[1]
    return _extract


@pytest.fixture(scope="function")
def bearer_token_header(extract_bearer_token):
    """
    Helper to create a complete Authorization header dict for API requests.
    
    Usage:
        token = "my_secret_key"
        headers = bearer_token_header(token)
        response = await api_client.get("/admin/info", headers=headers)
    """
    def _create_header(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _create_header


@pytest.fixture(scope="session")
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
    return mock_redis


@pytest.fixture(autouse=True, scope="function")
def mock_get_redis(mocked_redis):
    from app.database import get_redis

    async def _get_mock_redis():
        return mocked_redis

    app.dependency_overrides[get_redis] = _get_mock_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture(scope="session")
def setup_test_db(test_settings):
    from app.database.database import init_db
    init_db()  # Ensure global engine is initialized for tests
    
    settings = test_settings
    from app.database.database import engine
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
    if transaction.is_active:
        transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)
