from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql://music:music@localhost:5432/music"
    spotify_client_id: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"
    token_encryption_key: str = ""
    recent_poll_seconds: int = 300
    playback_poll_seconds: int = 30
    collector_enabled: bool = True


@lru_cache
def settings() -> Settings:
    return Settings()
