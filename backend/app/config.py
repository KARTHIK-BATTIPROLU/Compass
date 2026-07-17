from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = ""
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440
    groq_api_key: str = ""
    gemini_api_key: str = ""
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.mongodb_uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Copy backend/.env.example to backend/.env "
            "and set MONGODB_URI (e.g. mongodb://localhost:27017/edtech)."
        )
    return settings


def clear_settings_cache() -> None:
    get_settings.cache_clear()
