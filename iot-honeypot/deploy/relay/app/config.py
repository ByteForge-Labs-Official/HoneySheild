"""Runtime configuration for the side-car relay.

All values come from environment variables — secrets are injected via the
Docker secrets driver (`/run/secrets/...`) rather than baked into env vars.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RELAY_", env_file=None, extra="ignore")

    # ----- Source --------------------------------------------------------
    honeypot_db:    Path = Field(default=Path("/data/honeypot.db"))
    honeypot_log:   Path = Field(default=Path("/data/honeypot.log"))
    poll_interval_s: float = Field(default=10.0, ge=1.0, le=300.0)

    # ----- Postgres ------------------------------------------------------
    pg_dsn: str = Field(
        default="postgresql://relay:relay@postgres:5432/honeynet",
        description="DSN — the password comes from /run/secrets/postgres_password.",
    )

    # ----- Redis ---------------------------------------------------------
    redis_url: str = Field(default="redis://redis:6379/0")

    # ----- Observability -------------------------------------------------
    metrics_port: int = Field(default=9101)
    log_level:    str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()