"""Entrypoint for the relay.

Wires together:
  • config          — env-driven Settings
  • db_tail         — polls SQLite WAL, ships new rows to Postgres
  • log_tail        — inotify-watches /data/honeypot.log, JSON-decodes each line
  • metrics_server  — Prometheus exposition + /healthz on :9101
"""
from __future__ import annotations

import asyncio
import signal
from contextlib import asynccontextmanager

from prometheus_client import start_http_server
from app.config import get_settings
from app.metrics import INGEST_LAG_SECONDS, RELAY_UP
from app.streams import DbTail, LogTail


async def _amain() -> None:
    cfg = get_settings()

    # Prometheus / health endpoint.
    start_http_server(cfg.metrics_port)
    RELAY_UP.set(1)

    db  = DbTail(cfg)
    log = LogTail(cfg)

    stop = asyncio.Event()

    def _request_stop(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _request_stop)

    try:
        await asyncio.gather(db.run(stop), log.run(stop), heartbeat(stop))
    finally:
        RELAY_UP.set(0)
        INGEST_LAG_SECONDS.clear()


async def heartbeat(stop: asyncio.Event) -> None:
    """Tick the `relay_up` gauge so Prometheus can detect a frozen relay."""
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            continue


if __name__ == "__main__":
    asyncio.run(_amain())