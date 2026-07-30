"""Async SQLAlchemy sink for WARNING+ events.

Writes one row per event into ``audit_log`` (see
``app/db/models/audit_log.py``).  Buffering is per-instance — back-pressure
is handled by draining via ``asyncio.Queue`` + a background worker task,
so a slow DB never blocks the request thread.

Workers:

* Drain a bounded queue
* Use the same async DB session the rest of the app uses
* Never raise out of :meth:`emit` — errors are funneled to a fallback logger.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import structlog

try:
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover — SQLAlchemy optional in tests
    SQLAlchemyError = Exception  # type: ignore

from app.core.logging.fields import filter_dict

_log = structlog.get_logger("app.core.logging.handlers.database")


class DatabaseHandler(logging.Handler):
    """Async handler writing WARNING+ events to a database audit_log table.

    Parameters
    ----------
    queue_size:
        Maximum number of buffered records before back-pressure drops them.
    flush_interval:
        Seconds between automatic flushes when the queue is non-empty.
    min_level:
        Records below this level are dropped immediately.
    """

    def __init__(
        self,
        queue_size: int = 1000,
        flush_interval: float = 1.0,
        min_level: int = logging.WARNING,
    ) -> None:
        super().__init__(level=min_level)
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=queue_size)
        self._flush_interval = flush_interval
        self._stop_event = asyncio.Event()
        self._worker: asyncio.Task | None = None

    # ------------------------------------------------------------------ emit
    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = self._build_payload(record)
        except Exception:  # pragma: no cover — never raise from a log handler
            return
        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            # Drop with a warning rather than block the request thread
            _log.warning(
                "log.db.queue.full",
                event=payload.get("event"),
                queue_size=self._queue.maxsize,
            )
        self._ensure_worker()

    def _build_payload(self, record: logging.LogRecord) -> dict[str, Any]:
        # structlog-built records arrive with msg as a dict
        if isinstance(record.msg, dict):
            payload = dict(record.msg)
        else:
            payload = {"message": record.getMessage()}
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
        payload.setdefault("level", record.levelname.lower())
        payload.setdefault("logger", record.name)
        # exclude huge exception traceback from the DB row — keep the summary
        exc = payload.get("exception")
        if isinstance(exc, dict) and "traceback" in exc:
            payload["exception"] = {k: v for k, v in exc.items() if k != "traceback"}
        return filter_dict(payload)

    # --------------------------------------------------------------- worker
    def _ensure_worker(self) -> None:
        if self._worker is None or self._worker.done():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return  # no running loop yet — events will queue up
            self._worker = loop.create_task(self._run())

    async def _run(self) -> None:
        from app.db.session import async_session_maker  # local import — avoids cycles

        while not self._stop_event.is_set():
            try:
                payload = await asyncio.wait_for(self._queue.get(), timeout=self._flush_interval)
            except asyncio.TimeoutError:
                continue
            try:
                await self._persist(async_session_maker, payload)
            except Exception as exc:  # pragma: no cover — never raise
                _log.warning(
                    "log.db.persist.failed",
                    error=str(exc),
                    event=payload.get("event"),
                )
        # final drain
        while not self._queue.empty():
            payload = self._queue.get_nowait()
            try:
                await self._persist(async_session_maker, payload)
            except Exception as exc:  # pragma: no cover
                _log.warning("log.db.persist.failed", error=str(exc))

    @staticmethod
    async def _persist(async_session_maker, payload: dict[str, Any]) -> None:
        from app.db.models.audit_log import AuditLog  # local import

        async with async_session_maker() as session:
            row = AuditLog(
                timestamp=datetime.fromisoformat(payload["timestamp"]),
                level=payload.get("level", "info"),
                logger=payload.get("logger", "unknown"),
                event=payload.get("event", "log"),
                correlation_id=payload.get("correlation_id"),
                trace_id=payload.get("trace_id"),
                span_id=payload.get("span_id"),
                user_id=payload.get("user_id"),
                payload_json=json.dumps(payload, default=str, ensure_ascii=False),
            )
            session.add(row)
            await session.commit()

    # ------------------------------------------------------------------ api
    async def aclose(self) -> None:
        """Signal the worker to stop and drain remaining records."""
        self._stop_event.set()
        if self._worker is not None and not self._worker.done():
            try:
                await asyncio.wait_for(self._worker, timeout=5.0)
            except asyncio.TimeoutError:
                self._worker.cancel()