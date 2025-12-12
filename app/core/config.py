# -------------------------------------------------------
# Application Configuration Settings
# -------------------------------------------------------
# This module defines the application's configuration settings using Pydantic.
# Settings are loaded from environment variables via a .env file.
# The Settings class is a singleton accessed through the cached get_settings() function
# to ensure consistent configuration throughout the application lifecycle.
# -------------------------------------------------------

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    # Database connection URL for SQLAlchemy engine initialization.
    database_url: str = Field(default="postgresql://user:password@localhost/db")
    # Debug mode flag: enables SQL query logging and other debug features.
    debug: bool = False
    # Base URL of the application for constructing shortened and admin URLs.
    base_url: str
    # Host address the application binds to.
    host: str
    # Port number the application listens on.
    port: int
    # Environment name (e.g., 'development', 'production') for context-aware behavior.
    env_name: str
    # Configuration for loading settings from .env file.
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

@lru_cache
def get_settings() -> Settings:
    # Retrieve and cache the application settings.
    # The lru_cache decorator ensures this function is called only once,
    # returning the same Settings instance on subsequent calls.
    try:
        settings = Settings()
        
    except Exception as e:
        # Raise an error if settings cannot be loaded from the environment.
        raise e(f"Error loading settings: {e}")

    return settings