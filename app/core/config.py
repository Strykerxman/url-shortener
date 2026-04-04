# -------------------------------------------------------
# Application Configuration Settings
# -------------------------------------------------------
# This module defines the application's configuration settings using Pydantic.
# Settings are loaded from environment variables and optional .env files.
# The cached settings object can be cleared in tests to avoid config leakage.
# -------------------------------------------------------

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_user: str = Field(default="urlshortener", env="DATABASE_USER")
    database_pw: str = Field(default="changeme", env="DATABASE_PW")
    database_name: str = Field(default="urlshortener_db", env="DATABASE_NAME")
    debug: bool = False
    base_url: str = Field(default="http://127.0.0.1:8000", env="BASE_URL")
    env_name: str = Field(default="development", env="ENV_NAME")
    database_url: str = Field(..., env="DATABASE_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()