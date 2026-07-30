"""App-level gauges — dependencies, websockets, unhandled exceptions."""

from __future__ import annotations

from app.core.monitoring.metrics import (
    honeynet_app_active_websockets,
    honeynet_app_dependency_up,
    honeynet_app_exception_total,
)


def init() -> None:
    for dep in ("postgres", "redis", "mqtt_broker", "elasticsearch"):
        honeynet_app_dependency_up.labels(dependency=dep).set(0)
    honeynet_app_active_websockets.labels(endpoint="-").set(0)


def mark_dependency(name: str, up: bool) -> None:
    honeynet_app_dependency_up.labels(dependency=name).set(1 if up else 0)


def inc_websocket(endpoint: str) -> None:
    honeynet_app_active_websockets.labels(endpoint=endpoint).inc()


def dec_websocket(endpoint: str) -> None:
    honeynet_app_active_websockets.labels(endpoint=endpoint).dec()


def inc_exception(exc_type: str, path: str) -> None:
    honeynet_app_exception_total.labels(type=exc_type, path=path).inc()
