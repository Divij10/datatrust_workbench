from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded exclusively from the process environment or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DATATRUST_", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    max_upload_size_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    max_rows: int = Field(default=100_000, gt=0)
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
