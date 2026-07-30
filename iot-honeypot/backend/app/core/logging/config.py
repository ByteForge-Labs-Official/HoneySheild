"""Bootstraps structlog + stdlib logging.

Idempotent.  Called once from :func:`app.main.lifespan` and from the Celery
worker entrypoint.

Pipeline
========

* structlog processors — see :func:`app.core.logging.formatter.get_shared_processors`
* stdlib ``logging`` runs through ``ProcessorFormatter`` so its loggers
  (``uvicorn``, ``sqlalchemy``, ``celery``) share the same envelope
* Handlers: console (pretty/JSON), rotating file, optional DB sink,
  optional Sentry / OpenTelemetry handlers injected by the caller
"""
from __future__ import annotations

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Iterable

import structlog
from structlog.stdlib import ProcessorFormatter

from app.core.config import get_settings
from app.core.logging.exception_logger import ExceptionLogger
from app.core.logging.formatter import (
    HoneynetJsonFormatter,
    get_shared_processors,
)
from app.core.logging.handlers.console import (
    JsonStreamHandler,
    RichConsoleHandler,
)
from app.core.logging.handlers.database import DatabaseHandler
from app.core.logging.handlers.file import RotatingFileHandler

# A single global flag so the function is idempotent across reloads.
_CONFIGURED = False
_DB_HANDLER: DatabaseHandler | None = None


def _auto_json() -> bool:
    s = get_settings()
    if s.log_json is None:
        return s.app_env in {"staging", "production", "test"}
    return s.log_json


def _build_console_handler(json_mode: bool) -> logging.Handler:
    if json_mode:
        return JsonStreamHandler(stream=sys.stdout, level=logging.DEBUG)
    return RichConsoleHandler(stream=sys.stdout, level=logging.DEBUG)


def _build_file_handler(json_mode: bool) -> logging.Handler | None:
    s = get_settings()
    path = Path(s.log_dir) / s.log_file_name
    return RotatingFileHandler(
        path,
        max_bytes=s.log_rotation_max_bytes,
        backup_count=s.log_rotation_backup_count,
        level=getattr(logging, s.log_file_level),
    )


def _build_db_handler() -> DatabaseHandler | None:
    s = get_settings()
    global _DB_HANDLER
    if not s.log_to_db:
        return None
    if _DB_HANDLER is not None:
        return _DB_HANDLER
    _DB_HANDLER = DatabaseHandler(
        queue_size=int(os.getenv("LOG_DB_QUEUE", "1000")),
        flush_interval=float(os.getenv("LOG_DB_FLUSH", "1.0")),
    )
    return _DB_HANDLER


def configure_logging(
    *,
    level: str | None = None,
    json: bool | None = None,
    extra_handlers: Iterable[logging.Handler] = (),
    install_exception_hooks: bool = True,
) -> None:
    """Initialise structlog + stdlib logging. Safe to call more than once."""
    global _CONFIGURED
    s = get_settings()
    json_mode = json if json is not None else _auto_json()
    log_level = (level or s.log_level or "INFO").upper()

    # --------------------------------------------------------------- structlog
    shared = get_shared_processors() + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    structlog.configure(
        processors=shared,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # --------------------------------------------------------------- stdlib
    handlers: dict[str, dict] = {
        "console": {
            "()": lambda: _build_console_handler(json_mode),
            "level": log_level,
        },
        "file": {
            "()": lambda: _build_file_handler(json_mode) if _build_file_handler(json_mode) else logging.NullHandler(),
            "level": getattr(logging, s.log_file_level),
        },
        "exception": {
            "()": ExceptionLogger,
            "level": "WARNING",
        },
    }

    # Optional DB handler
    db = _build_db_handler()
    if db is not None:
        handlers["db"] = {"()": lambda: db, "level": "WARNING"}

    # Caller-supplied custom handlers (Sentry, OpenTelemetry, …)
    for idx, h in enumerate(extra_handlers):
        handlers[f"extra_{idx}"] = {"()": (lambda h: lambda: h)(h)}

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": HoneynetJsonFormatter},
        },
        "handlers": handlers,
        "loggers": {
            # Quiet noisy libs
            "uvicorn.error": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            "sqlalchemy.engine": {"level": "WARNING", "handlers": ["console", "file"], "propagate": False},
            "celery": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            "alembic": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            "": {  # root
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": s.log_propagate,
            },
        },
    }
    logging.config.dictConfig(config)
    logging.captureWarnings(True)

    # --------------------------------------------------------------- exception
    if install_exception_hooks:
        try:
            from app.core.logging.exception_logger import (
                install_asyncio_exception_handler,
                install_celery_failure_signal,
                install_sys_excepthook,
            )
            install_sys_excepthook()
            install_celery_failure_signal()
            try:
                install_asyncio_exception_handler()
            except RuntimeError:
                pass  # no running loop (Celery worker)
        except Exception:  # pragma: no cover
            pass

    _CONFIGURED = True


def is_configured() -> bool:
    return _CONFIGURED


def get_db_handler() -> DatabaseHandler | None:
    return _DB_HANDLER