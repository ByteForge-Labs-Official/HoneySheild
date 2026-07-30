"""
Centralised typed configuration loaded from environment / .env file.

Uses pydantic-settings v2 with a singleton accessor `get_settings()` so any
module can import settings cheaply without re-parsing.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- runtime --------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "honeynet-api"
    app_version: str = "1.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- logging --------------------------------------------------------
    log_json: bool | None = None  # None => auto (json in staging/production)
    log_dir: str = "/tmp/honeynet/logs"
    log_file_name: str = "honeynet.log"
    log_file_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_rotation_max_bytes: int = 50 * 1024 * 1024  # 50 MB
    log_rotation_backup_count: int = 10
    log_retention_days: int = 30
    log_to_db: bool = False  # write WARNING+ to `audit_log` table
    log_slow_request_ms: int = 750
    log_propagate: bool = False
    correlation_header: str = "x-correlation-id"
    traceparent_header: str = "traceparent"

    # --- security -------------------------------------------------------
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 30
    jwt_refresh_ttl_days: int = 7
    session_secret: SecretStr
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    # --- database -------------------------------------------------------
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "honeynet"
    postgres_user: str = "honeynet"
    postgres_password: SecretStr
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # --- redis / celery -------------------------------------------------
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn
    flower_user: str = "flower"
    flower_password: SecretStr

    # --- mqtt / integrations -------------------------------------------
    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: SecretStr | None = None

    ids_suricata_eve_url: str = "http://suricata:4760/eve.json"
    ids_zeek_log_dir: str = "/var/log/zeek"

    openai_api_key: SecretStr | None = None
    ollama_host: str = "http://ollama:11434"

    geoip_db_path: str = "/data/GeoLite2/GeoLite2-City.mmdb"

    # --- derived --------------------------------------------------------
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy URL pointing at the Postgres primary."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password.get_secret_value(),
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL used by Alembic migrations."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=self.postgres_user,
                password=self.postgres_password.get_secret_value(),
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def _split_csv(cls, value):
        """Allow `CORS_ORIGINS=http://a,http://b` in env files."""
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide singleton accessor for typed settings."""
    return Settings()  # type: ignore[call-arg]
