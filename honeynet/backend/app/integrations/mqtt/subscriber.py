"""MQTT subscriber that ingests honeypot-attacker traffic from the bait broker."""
from __future__ import annotations

import asyncio
from typing import Any

import aiomqtt
import orjson
import structlog

from app.core.config.constants import QUEUE_INGEST
from app.core.config.settings import get_settings
from app.services.ingest.normalizer import publish_attack

logger = structlog.get_logger()


async def run_subscriber(stop: asyncio.Event | None = None) -> None:
    s = get_settings()
    async with aiomqtt.Client(
        hostname=s.mqtt_host,
        port=s.mqtt_port,
        username=s.mqtt_user,
        password=s.mqtt_pass.get_secret_value(),
        identifier="honeynet-ingest",
    ) as client:
        await client.subscribe("#")   # catch-all for the bait broker
        async for msg in client.messages:
            if stop and stop.is_set():
                break
            try:
                payload: dict[str, Any] = orjson.loads(msg.payload or b"{}")
                payload.setdefault("topic", str(msg.topic))
                payload.setdefault("ts",    asyncio.get_event_loop().time())
                await publish_attack(payload)
            except Exception as e:    # noqa: BLE001
                logger.error("mqtt.subscriber.bad", error=str(e))