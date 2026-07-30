"""Centralized settings (pydantic-settings, env-driven)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- core --------------------------------------------------------
    app_env: str = Field("development", validation_alias="APP_ENV")
    log_level: str = Field("INFO",      validation_alias="LOG_LEVEL")
    project_root: Path = Path(__file__).resolve().parents[3]

    # --- backend -----------------------------------------------------
    backend_host: str = Field("0.0.0.0", validation_alias="BACKEND_HOST")
    backend_port: int = Field(8000,      validation_alias="BACKEND_PORT")
    backend_workers: int = Field(2,      validation_alias="BACKEND_WORKERS")
    cors_origins: list[str] = Field(default_factory=list, validation_alias="BACKEND_CORS_ORIGINS")
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    # --- secrets -----------------------------------------------------
    jwt_secret: SecretStr = Field(...,  validation_alias="JWT_SECRET")
    jwt_alg: str         = Field("HS256", validation_alias="JWT_ALG")
    jwt_access_ttl_min:  int = Field(60,   validation_alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(7,   validation_alias="JWT_REFRESH_TTL_DAYS")
    session_secret: SecretStr = Field(..., validation_alias="JWT_SECRET")

    # --- data --------------------------------------------------------
    postgres_dsn: PostgresDsn = Field(..., validation_alias="POSTGRES_DSN")
    redis_dsn:    RedisDsn    = Field(..., validation_alias="REDIS_DSN")
    mqtt_host:    str = Field(..., validation_alias="MQTT_HOST")
    mqtt_port:    int = Field(1883, validation_alias="MQTT_PORT")
    mqtt_user:    str = Field(..., validation_alias="MQTT_ADMIN_USER")
    mqtt_pass:    SecretStr = Field(..., validation_alias="MQTT_ADMIN_PASSWORD")

    # --- ai ----------------------------------------------------------
    ai_provider: str = Field("local", validation_alias="AI_PROVIDER")
    openai_api_key: SecretStr | None = Field(None, validation_alias="OPENAI_API_KEY")
    ollama_base_url: str = Field("http://ollama:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str    = Field("llama3.1:8b", validation_alias="OLLAMA_MODEL")

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            v = [s.strip() for s in v.split(",") if s.strip()]
        return v or []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
