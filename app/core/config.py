# -------------------------------------------------------
# Application Configuration Settings
# -------------------------------------------------------
# This module defines the application's configuration settings using Pydantic.
# Settings are loaded from environment variables via a .env file.
# The Settings class is a singleton accessed through the cached get_settings() function
# to ensure consistent configuration throughout the application lifecycle.
# -------------------------------------------------------

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from functools import lru_cache


class Settings(BaseSettings):
    # Configuration for loading settings from .env files.
    # .env.local takes precedence over .env, so local dev can override Docker defaults.
    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # Database username — used only by Docker Compose to initialise the Postgres container.
    # The Python application always connects via DATABASE_URL.
    database_user: str = "urlshortener"
    # Database password — same note as above.
    database_pw: str = "changeme"
    # Database name — same note as above.
    database_name: str = "urlshortener_db"
    # Debug mode flag: enables SQL query logging and other debug features.
    debug: bool = False
    # Base URL of the application for constructing shortened and admin URLs.
    base_url: str = "http://127.0.0.1:8000"
    # Environment name for context-aware behaviour.
    env_name: str = "development"
    # Database connection URL for SQLAlchemy engine initialisation.
    database_url: str
    # Redis server host for caching and session management.
    redis_host: str = "localhost"
    # Redis server port
    redis_port: int = 6379

    @computed_field(return_type=str)
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        else:
            raise ValueError("DATABASE_URL is required")


@lru_cache
def get_settings() -> Settings:
    # Retrieve and cache the application settings.
    # The lru_cache decorator ensures this function is called only once,
    # returning the same Settings instance on subsequent calls.
    try:
        settings = Settings()

    except Exception:
        raise
    return settings
