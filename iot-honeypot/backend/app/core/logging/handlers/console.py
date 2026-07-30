"""Console handlers — pretty (dev) or JSON (prod)."""
from __future__ import annotations

import logging
import sys

from app.core.logging.formatter import HoneynetConsoleFormatter, HoneynetJsonFormatter


class RichConsoleHandler(logging.StreamHandler):
    """Human-readable, colourised stdout handler (development)."""

    def __init__(self, stream=None, level: int = logging.NOTSET) -> None:
        super().__init__(stream or sys.stdout)
        self.setLevel(level)
        self.setFormatter(HoneynetConsoleFormatter())


class JsonStreamHandler(logging.StreamHandler):
    """Single-line JSON to stdout (production)."""

    def __init__(self, stream=None, level: int = logging.NOTSET) -> None:
        super().__init__(stream or sys.stdout)
        self.setLevel(level)
        self.setFormatter(HoneynetJsonFormatter())