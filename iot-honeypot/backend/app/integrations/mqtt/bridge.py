"""Async MQTT bridge - subscribes to honeypot topics and forwards events."""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

import aiomqtt

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class MqttBridge:
    """Subscribe to MQTT topics that honeypots publish to, fan out to handlers."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._handlers: dict[str, list] = {}

    def subscribe(self, topic: str, handler) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    async def _run(self) -> None:
        s = get_settings()
        kwargs = dict(hostname=s.mqtt_host, port=s.mqtt_port, keepalive=60)
        if s.mqtt_username:
            kwargs["username"] = s.mqtt_username
            pw = s.mqtt_password.get_secret_value() if s.mqtt_password else None
            if pw:
                kwargs["password"] = pw
        while not self._stop.is_set():
            try:
                async with aiomqtt.Client(**kwargs) as client:
                    for topic in self._handlers:
                        await client.subscribe(topic)
                    log.info("mqtt.connected", host=s.mqtt_host, port=s.mqtt_port)
                    async for msg in client.messages:
                        await self._dispatch(msg)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.warning("mqtt.disconnected", error=str(e))
                await asyncio.sleep(3)

    async def _dispatch(self, msg) -> None:
        for topic, handlers in self._handlers.items():
            if aiomqtt.matches_topic(msg.topic, topic):
                try:
                    payload = json.loads(msg.payload.decode("utf-8", "replace"))
                except Exception:
                    payload = {"raw": msg.payload.decode("utf-8", "replace", errors="replace")}
                for h in handlers:
                    try:
                        await h(topic=msg.topic, payload=payload)
                    except Exception as e:  # noqa: BLE001
                        log.warning("mqtt.handler_error", error=str(e), topic=msg.topic)

    async def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name="mqtt-bridge")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


mqtt_bridge = MqttBridge()