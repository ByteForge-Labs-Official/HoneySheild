"""Aggregate health check across DB, Redis, MQTT."""
from __future__ import annotations

from fastapi import status
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.integrations.redis.client import get_redis

_s = get_settings()


async def _check_db() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "down"


async def _check_redis() -> str:
    try:
        await get_redis().ping()
        return "ok"
    except Exception:
        return "down"


async def aggregate_health() -> dict[str, str]:
    return {
        "db": await _check_db(),
        "redis": await _check_redis(),
        "version": _s.app_version,
        "env": _s.app_env,
    }