from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    llm_api_key: str
    frontend_url: str = "http://localhost:3000"
    base_url: str

    class Config:
        env_file = str(_ENV_PATH)
        extra = "ignore"

@lru_cache
def get_settings():
    return Settings()
