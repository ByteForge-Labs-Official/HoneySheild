"""Ingest pipeline metrics."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from app.core.monitoring.metrics import (
    honeynet_event_ingest_duration_seconds,
    honeynet_events_ingested_total,
    honeynet_events_rejected_total,
)


def init() -> None:
    """Initialise the ingest collector.

    Currently a no-op — Prometheus counters are zero-initialised.  Kept
    as a hook so we can pre-warm label sets later if needed.
    """
    # Touch the metrics so they appear in the registry even with zero
    # observations on first scrape (helps Grafana pick them up).
    honeynet_events_ingested_total.labels(honeypot="-", protocol="-", severity="-").inc(0)
    honeynet_events_rejected_total.labels(honeypot="-", reason="-").inc(0)


def observe_event(honeypot: str, protocol: str, severity: str) -> None:
    """Record a successful ingest."""
    honeynet_events_ingested_total.labels(
        honeypot=honeypot, protocol=protocol, severity=severity
    ).inc()


def observe_rejection(honeypot: str, reason: str) -> None:
    """Record a rejected event (validation / size / auth)."""
    honeynet_events_rejected_total.labels(honeypot=honeypot, reason=reason).inc()


@contextmanager
def time_ingest(honeypot: str, protocol: str) -> Iterator[None]:
    """Context manager wrapping a single ingest for latency observation."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        honeynet_event_ingest_duration_seconds.labels(
            honeypot=honeypot, protocol=protocol
        ).observe(elapsed)
