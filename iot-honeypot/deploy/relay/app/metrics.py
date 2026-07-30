"""Prometheus metric definitions for the relay.

Kept tiny — the relay is observability infrastructure, not a domain service.
"""
from __future__ import annotations

from prometheus_client import Gauge, Counter

RELAY_UP = Gauge(
    "relay_up",
    "1 if the relay is running, 0 if it has exited.",
)

INGEST_LAG_SECONDS = Gauge(
    "relay_ingest_lag_seconds",
    "Seconds since the relay last saw a new row in the honeypot database.",
)

EVENTS_SHIPPED_TOTAL = Counter(
    "relay_events_shipped_total",
    "Events forwarded to Postgres.",
    labelnames=("source",),   # db | log
)

SHIP_ERRORS_TOTAL = Counter(
    "relay_ship_errors_total",
    "Errors while forwarding to Postgres / Redis.",
    labelnames=("target", "kind"),
)