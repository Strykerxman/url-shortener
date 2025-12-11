from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = Field(default="postgresql://user:password@localhost/db", alias="DATABASE_URL")
    debug: bool = False
    host: str
    port: int
    env_name: str
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

@lru_cache
def get_settings() -> Settings:
    try:
        settings = Settings()
        
    except Exception as e:
        raise e(f"Error loading settings: {e}")

    return settings

