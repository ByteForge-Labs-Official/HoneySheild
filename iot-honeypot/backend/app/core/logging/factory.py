"""Slim wrapper around :mod:`structlog` so callers depend on a stable surface."""
from __future__ import annotations

from typing import Any, Iterable

import structlog

from app.core.logging.context import bind_context


def get_logger(name: str | None = None, **bound) -> Any:
    """Return a bound structlog logger.

    ```python
    log = get_logger(__name__)
    log.info("auth.login", user_id=u.id)

    log2 = get_logger(__name__, request_id=req.id)  # pre-bound
    log2.info("attack.ingest", source_ip="1.2.3.4")
    ```
    """
    if bound:
        bind_context(**bound)
    logger = structlog.get_logger(name) if name else structlog.get_logger()
    return logger


def bind_loggers(names: Iterable[str], **bound) -> list[Any]:
    """Bind the same context to several logger names in one call."""
    bind_context(**bound)
    return [structlog.get_logger(n) for n in names] if name else [structlog.get_logger()]  # noqa: F821