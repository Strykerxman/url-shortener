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
    # Database username for authentication.
    database_user: str = Field(..., env="DATABASE_USER")
    # Database password for authentication.
    database_pw: str = Field(..., env="DATABASE_PW")
    # Database name to connect to.
    database_name: str = Field(..., env="DATABASE_NAME")
    # Debug mode flag: enables SQL query logging and other debug features.
    debug: bool = False
    # Base URL of the application for constructing shortened and admin URLs.
    base_url: str
    # Environment name for context-aware behavior.
    env_name: str
    # Database connection URL for SQLAlchemy engine initialization.
    # This can be overridden via DATABASE_URL env variable, otherwise defaults to localhost postgres.
    database_url: str = Field(default="", env="DATABASE_URL")
    # Configuration for loading settings from .env file.
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # If DATABASE_URL not provided, construct it from individual components
        if not self.database_url or self.database_url == "":
            self.database_url = f"postgresql://{self.database_user}:{self.database_pw}@localhost:5432/{self.database_name}"

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