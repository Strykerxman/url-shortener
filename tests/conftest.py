import pytest
from unittest.mock import AsyncMock
from collections import defaultdict

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

from redis.asyncio import Redis

from app.main import app
from app.database import get_db, get_redis
from app.core.config import get_settings

class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding='utf-8',
        extra="ignore"
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
    
@pytest.fixture(scope="session")
def test_settings():
    return TestSettings()

@pytest.fixture(autouse=True,scope="function")
def override_get_settings(test_settings):
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.pop(get_settings, None)

@pytest.fixture(scope="session")
def mocked_redis():
    storage = defaultdict(lambda: None)
    mock_redis = AsyncMock(spec=Redis)

    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()

    mock_redis.get.side_effect = lambda key: storage.get(key)
    mock_redis.set.side_effect = lambda key, val, ex=3600*24: storage.update({key: val}) or True
    mock_redis.delete.side_effect = lambda key: storage.pop(key, None) is not None
    
    mock_redis.ping = AsyncMock()
    return mock_redis

@pytest.fixture(autouse=True, scope="function")
def mock_get_redis(mocked_redis):
    async def _get_mock_redis():
        return mocked_redis
    
    app.dependency_overrides[get_redis] = _get_mock_redis
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
