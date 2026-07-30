"""Structured logging via loguru + structlog bridge."""
from __future__ import annotations

import logging
import sys

import structlog
from loguru import logger as _loguru


def configure_logging(level: str = "INFO") -> None:
    _loguru.remove()
    _loguru.add(
        sys.stdout,
        serialize=True,
        backtrace=False,
        diagnose=False,
        level=level,
        enqueue=True,
        colorize=False,
    )

    class _Intercept(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = _loguru.level(record.levelname).name
            except ValueError:
                level = record.levelname
            _loguru.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    logging.root.handlers = [_Intercept()]
    logging.root.setLevel(level)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
