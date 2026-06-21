from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # Database
    database_url: PostgresDsn

    # Redis
    redis_url: RedisDsn

    # LLM
    llm_model_path: str
    llm_n_ctx: int = Field(default=4096, gt=0)
    llm_n_threads: int = Field(default=4, gt=0)
    llm_n_gpu_layers: int = Field(default=0, ge=0)

    # App
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()