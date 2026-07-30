"""Custom structlog and stdlib formatters.

* `HoneynetJsonFormatter` — single-line JSON, fixed envelope ordering.
* `HoneynetConsoleFormatter` — human-readable, colourised for dev.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import socket
import sys
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.logging.fields import filter_dict

# ---------------------------------------------------------------------------
# Envelope keys written first so they line up across services.
# ---------------------------------------------------------------------------
ENVELOPE_ORDER: tuple[str, ...] = (
    "timestamp", "level", "logger", "event",
    "app", "env", "version", "pid", "hostname", "thread",
    "correlation_id", "request_id", "trace_id", "span_id", "parent_span_id",
)

_HOSTNAME = socket.gethostname()


# ---------------------------------------------------------------------------
# structlog processors
# ---------------------------------------------------------------------------
def _add_envelope(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Inject app/env/version/pid/hostname/thread on every event."""
    s = get_settings()
    event_dict.setdefault("app", s.app_name)
    event_dict.setdefault("env", s.app_env)
    event_dict.setdefault("version", s.app_version)
    event_dict.setdefault("pid", os.getpid())
    event_dict.setdefault("hostname", _HOSTNAME)
    try:
        import threading
        event_dict.setdefault("thread", threading.current_thread().name)
    except Exception:  # pragma: no cover
        pass
    return event_dict


def _normalise_types(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Coerce datetime/UUID/Decimal to JSON-safe primitives."""
    for k, v in list(event_dict.items()):
        if isinstance(v, _dt.datetime):
            event_dict[k] = (
                v.isoformat(timespec="milliseconds")
                if v.tzinfo
                else v.replace(tzinfo=_dt.timezone.utc).isoformat(timespec="milliseconds")
            )
        elif isinstance(v, _dt.date):
            event_dict[k] = v.isoformat()
        elif isinstance(v, set):
            event_dict[k] = sorted(v)
    return event_dict


def _scrub(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact well-known sensitive keys."""
    return filter_dict(event_dict)


def _order_envelope(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Reorder dict so envelope keys come first (debug-friendly JSON)."""
    extras = {k: v for k, v in event_dict.items() if k not in ENVELOPE_ORDER}
    head = {k: event_dict[k] for k in ENVELOPE_ORDER if k in event_dict}
    head.update(extras)
    return head


# ---------------------------------------------------------------------------
# Stdlib formatter (single line of JSON)
# ---------------------------------------------------------------------------
class HoneynetJsonFormatter(logging.Formatter):
    """Stdlib-side formatter. Produces one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        # structlog events arrive via `record.msg` as a dict after
        # ProcessorFormatter has run; otherwise we build the dict ourselves.
        if isinstance(record.msg, dict):
            payload = dict(record.msg)
        else:
            payload = {
                "message": record.getMessage(),
                "level": record.levelname.lower(),
                "logger": record.name,
            }

        # promote structlog record-attrs that survived stdlib formatting
        for attr in (
            "timestamp", "event", "app", "env", "version", "pid",
            "hostname", "thread", "correlation_id", "request_id",
            "trace_id", "span_id", "parent_span_id",
        ):
            value = getattr(record, attr, None)
            if value is not None:
                payload.setdefault(attr, value)

        if record.exc_info:
            payload.setdefault("exception", self.formatException(record.exc_info))

        # Make sure base fields are present even when this formatter is hit
        # directly by a stdlib logger (e.g. SQLAlchemy, uvicorn).
        payload.setdefault("timestamp", _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"))
        payload.setdefault("level", record.levelname.lower())
        payload.setdefault("logger", record.name)
        payload.setdefault("thread", payload.get("thread"))

        payload = filter_dict(payload)
        return json.dumps(_order_envelope({}, "", payload), default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Console formatter (dev only — colourised, multi-line)
# ---------------------------------------------------------------------------
class HoneynetConsoleFormatter(logging.Formatter):
    """Pretty, single-line, colourised formatter for `stdout` in dev."""

    LEVEL_COLORS = {
        "DEBUG": "\x1b[90m",
        "INFO": "\x1b[36m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[1;41m",
    }
    RESET = "\x1b[0m"
    DIM = "\x1b[2m"
    BOLD = "\x1b[1m"

    def format(self, record: logging.LogRecord) -> str:
        ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        level = record.levelname
        colour = self.LEVEL_COLORS.get(level, "")
        logger = record.name
        # event vs message
        event = getattr(record, "event", None)
        message = event or record.getMessage()
        cid = getattr(record, "correlation_id", None)

        line = (
            f"{self.DIM}{ts}{self.RESET} "
            f"{colour}{self.BOLD}{level:<8}{self.RESET} "
            f"{self.DIM}{logger}{self.RESET} "
            f"{message}"
        )
        if cid:
            line += f"  {self.DIM}cid={cid}{self.RESET}"

        extras = []
        for k, v in record.__dict__.items():
            if k.startswith("_") or k in (
                "args", "msg", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
            ):
                continue
            if k in {"event", "correlation_id", "request_id"}:
                continue
            extras.append(f"{self.DIM}{k}={v!r}{self.RESET}")
        if extras:
            line += "  " + " ".join(extras)

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


# ---------------------------------------------------------------------------
# Public processor lists
# ---------------------------------------------------------------------------
def get_shared_processors() -> list:
    """Processors shared between dev and prod rendering."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _normalise_types,
        _add_envelope,
        _scrub,
        _order_envelope,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def get_json_renderer():
    return structlog.processors.JSONRenderer(serializer=_json_dumps_safe)


def _json_dumps_safe(obj, **kw) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False, **kw)