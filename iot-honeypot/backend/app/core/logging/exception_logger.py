"""Glue unhandled exceptions into the central logging pipeline.

* ``sys.excepthook`` -> asyncio ``loop.set_exception_handler``
* ``celery`` ``task_failure`` signal
* ``logging.Handler`` subclass (``ExceptionLogger``) — log.error(exc_info=True)

All three funnel through the same `log_exception` helper so the formatter sees
the canonical ``exc_type``, ``exc_message`` and ``exception`` fields.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import traceback
from typing import Any

import structlog

from app.core.logging.fields import filter_dict

_log = structlog.get_logger("app.core.logging.exceptions")


def _format(exc_type, exc_value, exc_tb) -> dict[str, Any]:
    frames = traceback.format_exception(exc_type, exc_value, exc_tb)
    return {
        "exc_type": getattr(exc_type, "__qualname__", str(exc_type)),
        "exc_message": str(exc_value),
        "exception": {
            "type": getattr(exc_type, "__qualname__", str(exc_type)),
            "value": str(exc_value),
            "traceback": "".join(frames).splitlines(),
        },
    }


def log_exception(
    exc_type=type(None),
    exc_value: BaseException | None = None,
    exc_tb=None,
    *,
    where: str = "process",
    **extra,
) -> None:
    """Format + emit an exception event through the bound logger."""
    payload: dict[str, Any] = {"event": "exception.unhandled", "where": where}
    payload.update(_format(exc_type, exc_value, exc_tb))
    payload.update(filter_dict(extra))
    _log.critical(**payload)


def install_sys_excepthook() -> None:
    """Replace ``sys.excepthook`` with one that logs through structlog."""

    def _hook(exc_type, exc_value, exc_tb):
        log_exception(exc_type, exc_value, exc_tb, where="sys.excepthook")

    sys.excepthook = _hook


def install_asyncio_exception_handler(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Route asyncio's unhandled task exceptions into our pipeline."""
    loop = loop or asyncio.get_event_loop()

    def _handler(_context: dict[str, Any]) -> None:
        exc = _context.get("exception")
        if isinstance(exc, BaseException):
            log_exception(
                type(exc),
                exc,
                exc.__traceback__,
                where="asyncio",
                task=_context.get("task"),
                message=_context.get("message"),
            )
        else:
            _log.error(
                "exception.unhandled",
                where="asyncio",
                message=_context.get("message"),
                context=str(_context),
            )

    loop.set_exception_handler(_handler)


def install_celery_failure_signal() -> None:
    """Push Celery ``task_failure`` events into our pipeline."""
    try:
        from celery import signals  # type: ignore
    except ImportError:  # pragma: no cover — Celery optional in unit tests
        return

    def _on_failure(
        task_id: str,
        exception: BaseException,
        traceback=None,  # noqa: A002 — Celery signature
        einfo=None,
        sender=None,
        **kwargs,
    ):
        log_exception(
            type(exception),
            exception,
            getattr(exception, "__traceback__", None),
            where="celery",
            task_id=task_id,
            task_name=getattr(sender, "name", None),
            queue=getattr(sender, "queue", None) if sender else None,
            einfo=str(einfo) if einfo else None,
        )

    signals.task_failure.connect(_on_failure, weak=False)


class ExceptionLogger(logging.Handler):
    """logging.Handler subclass that funnels records with ``exc_info`` into structlog."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if not record.exc_info:
                return
            logger = structlog.get_logger(record.name)
            kwargs: dict[str, Any] = {
                "event": "logging.exception",
                "exc_type": record.exc_info[0].__qualname__ if record.exc_info[0] else None,
                "exc_message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
            if record.exc_info[2]:
                kwargs["exception"] = {
                    "type": kwargs["exc_type"],
                    "value": kwargs["exc_message"],
                    "traceback": traceback.format_tb(record.exc_info[2]),
                }
            logger.error(**{k: v for k, v in kwargs.items() if v is not None})
        except Exception:  # pragma: no cover — never raise from a log handler
            sys.stderr.write("ExceptionLogger itself failed\n")