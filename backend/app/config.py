from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TripGuard AI"
    http_timeout_seconds: float = 12.0
    ourairports_csv_url: str = "https://davidmegginson.github.io/ourairports-data/airports.csv"
    faa_nas_status_url: str | None = "https://nasstatus.faa.gov/api/airport-status-information"
    ai_provider: str = "none"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
