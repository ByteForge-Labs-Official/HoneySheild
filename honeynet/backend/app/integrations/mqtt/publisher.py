"""Async MQTT publisher used by operator endpoints (control of bait devices)."""
from __future__ import annotations

import asyncio
from typing import Any

import aiomqtt
import orjson
import structlog

from app.core.config.settings import get_settings

logger = structlog.get_logger()
_lock = asyncio.Lock()
_client: aiomqtt.Client | None = None


async def _client_singleton() -> aiomqtt.Client:
    global _client
    if _client is None:
        s = get_settings()
        _client = aiomqtt.Client(
            hostname=s.mqtt_host,
            port=s.mqtt_port,
            username=s.mqtt_user,
            password=s.mqtt_pass.get_secret_value(),
            keepalive=60,
            identifier="honeynet-backend",
        )
        await _client.__aenter__()
    return _client


async def publish(topic: str, payload: dict[str, Any], *, qos: int = 1, retain: bool = False,
                 username: str = "operator") -> None:
    async with _lock:
        try:
            c = await _client_singleton()
            await c.publish(topic, orjson.dumps(payload), qos=qos, retain=retain)
        except Exception as e:    # noqa: BLE001
            logger.error("mqtt.publish_failed", topic=topic, error=str(e))


async def shutdown() -> None:
    global _client
    if _client is not None:
        await _client.__aexit__(None, None, None)
        _client = None