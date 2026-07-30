"""ASGI middleware that:

* generates / propagates ``X-Correlation-ID`` (and W3C ``traceparent``)
* bound the values into :mod:`structlog.contextvars` for the request lifetime
* emits ``http.request.start`` and ``http.request.end`` (level: INFO,
  or WARNING when slower than ``LOG_SLOW_REQUEST_MS``)
* measures wall-clock duration and response size

Mounted in ``app/main.py``:

```python
app.add_middleware(CorrelationIdMiddleware)
```
"""
from __future__ import annotations

import logging
import re
import time
from typing import Awaitable, Callable, Iterable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging.context import (
    clear_context,
    new_trace_id,
    set_correlation_id,
    set_trace_id,
)

_log = structlog.get_logger("app.core.logging.middleware")
_trusted_proxies: tuple[str, ...] = ()

_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[a-f0-9]{2})-(?P<trace_id>[a-f0-9]{32})-"
    r"(?P<span_id>[a-f0-9]{16})-(?P<flags>[a-f0-9]{2})$"
)


def configure_trusted_proxies(cidrs: Iterable[str]) -> None:
    """Set the list of trusted X-Forwarded-For sources."""
    global _trusted_proxies
    _trusted_proxies = tuple(cidrs)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _parse_traceparent(header: str | None) -> tuple[str | None, str | None]:
    if not header:
        return None, None
    m = _TRACEPARENT_RE.match(header.strip())
    if not m:
        return None, None
    return m["trace_id"], m["span_id"]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Bind ``correlation_id`` + ``trace_id`` for every request and log lifecycle events."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        s = get_settings()
        # Clear any stale context (test re-runs, background tasks).
        clear_context()

        cid = request.headers.get(s.correlation_header) or request.headers.get("x-correlation-id")
        traceparent = (
            request.headers.get("traceparent")
            or request.headers.get(s.traceparent_header)
        )
        trace_id, span_id = _parse_traceparent(traceparent)

        # also handle the "trace id alone" header (lightweight distributed traces)
        if not trace_id:
            trace_id = request.headers.get("x-trace-id")

        cid = set_correlation_id(cid)
        if trace_id or span_id or traceparent:
            set_trace_id(
                trace_id=trace_id or new_trace_id(),
                span_id=span_id,
            )
        else:
            set_trace_id(new_trace_id(), None)

        bind_user: dict[str, str] = {}
        # Common auth-headers convention; cheap, no DB hit
        if request.headers.get("authorization"):
            bind_user["auth_kind"] = "bearer"

        start = time.perf_counter()
        method = request.method
        path_template = request.url.path
        status_code = 500
        content_length = 0

        _log.info(
            "http.request.start",
            method=method,
            path=path_template,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            **bind_user,
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
            content_length = int(response.headers.get("content-length", 0) or 0)
            response.headers[s.correlation_header] = cid
            response.headers["x-request-id"] = cid
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            log_method = _log.warning if duration_ms > s.log_slow_request_ms else _log.info
            log_method(
                "http.request.end",
                method=method,
                path=path_template,
                status_code=status_code,
                duration_ms=duration_ms,
                content_length=content_length,
                client_ip=_client_ip(request),
                **bind_user,
            )
            clear_context()


def install_request_logger(logger_name: str = "uvicorn.access") -> None:
    """Route ``uvicorn.access`` through the central pipeline."""
    access = logging.getLogger(logger_name)
    access.propagate = True
