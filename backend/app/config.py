"""Application configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://kawn:kawn_secret@localhost:5432/kawn_content_engine"
    database_url_sync: str = "postgresql://kawn:kawn_secret@localhost:5432/kawn_content_engine"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    secret_key: str = "dev-secret-key"
    cors_origins: str = "http://localhost:3000"
    scheduler_enabled: bool = True
    default_posts_per_day: int = 5

    ai_default_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    huggingface_api_key: str = ""
    huggingface_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    news_api_key: str = ""
    seed_sample_data: bool = False

    kawn_app_api_url: str = ""
    kawn_app_api_key: str = ""
    kawn_auto_publish: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
