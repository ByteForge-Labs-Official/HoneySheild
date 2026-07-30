"""Attack ingest normaliser.

Single choke-point that converts raw honeypot events into our canonical schema,
applies sanitisation, and emits them into Redis streams.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import orjson

from app.core.config.constants import (
    LIVE_ATTACKS_PUBSUB,
    MAX_LINE_LEN,
    MAX_TAGS,
    MAX_VALUE_LEN,
    RAW_ATTACKS_STREAM,
)
from app.core.security.sanitize import clean_line, clean_value
from app.integrations.redis.client import get_redis


async def normalize_string(value: str | None, *, cap: int = MAX_VALUE_LEN) -> str:
    return clean_value(value, cap=cap)


async def normalize_line(value: str | None) -> str:
    return clean_line(value, cap=MAX_LINE_LEN)


async def normalize_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate + sanitize a single attacker event before persistence."""
    return {
        "ts":        _safe_dt(payload.get("ts")),
        "kind":      clean_line(str(payload.get("kind", "unknown")), cap=32),
        "severity":  _severity(payload.get("severity", "info")),
        "src_ip":    (clean_value(payload.get("src_ip"),  cap=64) or None),
        "dst_ip":    (clean_value(payload.get("dst_ip"),  cap=64) or None),
        "dst_port":  _safe_int(payload.get("dst_port")),
        "protocol":  clean_line(str(payload.get("protocol", "unknown")), cap=16),
        "raw":       clean_line(payload.get("raw"), cap=8192),
        "meta":      {k: clean_value(v, cap=512) for k, v in (payload.get("meta") or {}).items()},
    }


async def publish_attack(canonical: dict[str, Any]) -> None:
    """Push to Redis stream + live pub/sub channel."""
    r = await get_redis()
    raw = orjson.dumps(canonical).decode()
    await r.xadd(RAW_ATTACKS_STREAM, {"payload": raw}, maxlen=10_000, approximate=True)
    await r.publish(LIVE_ATTACKS_PUBSUB, raw)


def _safe_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return datetime.now(timezone.utc)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _severity(value: Any) -> str:
    s = str(value).lower()
    return s if s in {"info", "low", "medium", "high", "critical"} else "info"


def clamp_tags(tags: list[str] | None) -> list[str]:
    return [clean_value(t, cap=80) for t in (tags or []) if t][:MAX_TAGS]