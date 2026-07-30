"""Async Redis client singleton."""
from __future__ import annotations

import redis.asyncio as aioredis
import structlog

from app.core.config.settings import get_settings

logger = structlog.get_logger()
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        s = get_settings()
        _redis = aioredis.from_url(
            str(s.redis_dsn),
            encoding="utf-8",
            decode_responses=True,
            max_connections=64,
            health_check_interval=30,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None