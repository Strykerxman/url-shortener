import os

# Deterministic test defaults before application imports.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["BASE_URL"] = "http://testserver"
os.environ["ENV_NAME"] = "test"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["DEBUG"] = "false"

import pytest


@pytest.fixture(scope="session", autouse=True)
def _configure_test_environment():
    """Keep test environment defaults stable for the full session."""
    yield


@pytest.fixture(scope="session")
def session_clear_settings_cache():
    """
    Clear the lru_cache on get_settings() at session end to prevent
    state leakage between sessions (useful when running tests multiple times in the same process).
    """
    yield
    from app.core.config import get_settings
    get_settings.cache_clear()
