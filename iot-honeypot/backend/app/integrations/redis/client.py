"""Async Redis client (process-wide singleton)."""
from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the process-wide async Redis client."""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            str(get_settings().redis_url),
            decode_responses=True,
            max_connections=64,
            health_check_interval=30,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None