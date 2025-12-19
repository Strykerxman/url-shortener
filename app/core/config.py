# -------------------------------------------------------
# Application Configuration Settings
# -------------------------------------------------------
# This module defines the application's configuration settings using Pydantic.
# Settings are loaded from environment variables via a .env file.
# The Settings class is a singleton accessed through the cached get_settings() function
# to ensure consistent configuration throughout the application lifecycle.
# -------------------------------------------------------

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from functools import lru_cache

ENV_FILE = os.getenv('ENV_FILE', '.env.local')

class Settings(BaseSettings):
    # Configuration for loading settings from .env file.
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8'
    )
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
    # Redis server host for caching and session management.
    redis_host: str = Field(..., env="REDIS_HOST")
    # Redis server port
    redis_port: int = Field(..., env="REDIS_PORT")
    
    
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

    except Exception as e:
        raise
    return settings

