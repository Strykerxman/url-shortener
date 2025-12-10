from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    base_url: str
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
        print("An error occured while loading the settings: {e}")

    return settings