"""Logging handlers.

* :class:`RichConsoleHandler` — pretty dev output
* :class:`JsonStreamHandler` — single-line JSON to stdout
* :class:`RotatingFileHandler` — file with size-based rotation
* :class:`DatabaseHandler` — async SQLAlchemy sink for WARNING+
"""
from app.core.logging.handlers.console import JsonStreamHandler, RichConsoleHandler
from app.core.logging.handlers.database import DatabaseHandler
from app.core.logging.handlers.file import (
    RotatingFileHandler,
    build_retention_cleanup,
)

__all__ = [
    "RichConsoleHandler",
    "JsonStreamHandler",
    "RotatingFileHandler",
    "DatabaseHandler",
    "build_retention_cleanup",
]