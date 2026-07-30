"""Aggregated health probe."""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text

from app.db.session import engine
from app.integrations.redis.client import get_redis

logger = structlog.get_logger()


async def aggregate_health() -> dict[str, Any]:
    """Returns {'status': 'ok'|'degraded'|'down', 'components': {...}}."""
    components: dict[str, dict[str, Any]] = {}
    overall = "ok"

    # postgres
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["postgres"] = {"status": "ok"}
    except Exception as e:   # noqa: BLE001
        components["postgres"] = {"status": "down", "error": type(e).__name__}
        overall = "down"

    # redis
    try:
        r = await get_redis()
        await r.ping()
        components["redis"] = {"status": "ok"}
    except Exception as e:   # noqa: BLE001
        components["redis"] = {"status": "down", "error": type(e).__name__}
        overall = "down"

    return {"status": overall, "components": components}