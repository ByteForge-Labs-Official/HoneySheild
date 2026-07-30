"""IDS feed metrics — populated as Suricata / Zeek alerts enter the backend."""

from __future__ import annotations

import time

from app.core.monitoring.metrics import (
    honeynet_ids_alerts_total,
    honeynet_ids_last_event_timestamp,
)


def init() -> None:
    honeynet_ids_alerts_total.labels(engine="-", severity="-").inc(0)


def observe(engine: str, severity: str) -> None:
    honeynet_ids_alerts_total.labels(engine=engine, severity=severity).inc()
    honeynet_ids_last_event_timestamp.labels(engine=engine).set(time.time())
