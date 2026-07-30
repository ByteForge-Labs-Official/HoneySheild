"""Request/task scoped context variables.

* ``correlation_id``  — propagates across HTTP requests and Celery tasks
* ``trace_id``        — W3C trace-context (32-hex chars)
* ``span_id``         — current span (16-hex chars)
* ``parent_span_id``  — caller span

Bound through :func:`structlog.contextvars.bind_contextvars` so every event
emitted by a structlog logger automatically carries the values — even when
the call site is one stack frame deep in a Celery worker.
"""
from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Iterator

import structlog

# ---------------------------------------------------------------------------
# ContextVars
# ---------------------------------------------------------------------------
correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "span_id", default=None
)
parent_span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "parent_span_id", default=None
)


# ---------------------------------------------------------------------------
# Helpers — public API
# ---------------------------------------------------------------------------
def new_correlation_id() -> str:
    return uuid.uuid4().hex


def new_trace_id() -> str:
    return uuid.uuid4().hex  # 32-hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]  # 16-hex


def set_correlation_id(value: str | None = None) -> str:
    """Bind a correlation id for the current task / request.

    Returns the value that was bound (generated one when ``value`` is falsy).
    """
    value = value or new_correlation_id()
    structlog.contextvars.bind_contextvars(
        correlation_id=value,
        request_id=value,  # legacy alias
    )
    return value


def set_trace_id(
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
) -> tuple[str, str]:
    """Bind a (trace_id, span_id) pair (W3C trace-context)."""
    trace_id = trace_id or new_trace_id()
    span_id = span_id or new_span_id()
    structlog.contextvars.bind_contextvars(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
    )
    return trace_id, span_id


def bind_context(**kwargs) -> None:
    """Arbitrary kwargs (e.g. ``user_id=…``) bound into the per-task context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Drop every key for the current task. Tests + Celery hooks call this."""
    structlog.contextvars.clear_contextvars()
    correlation_id_var.set(None)
    trace_id_var.set(None)
    span_id_var.set(None)
    parent_span_id_var.set(None)


def current_correlation_id() -> str | None:
    return correlation_id_var.get()


def current_trace_id() -> str | None:
    return trace_id_var.get()


@contextmanager
def correlation_scope(
    correlation_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
) -> Iterator[dict[str, str]]:
    """`with correlation_scope(cid=…):` — binds the values, restores on exit."""
    saved = {
        "correlation_id": correlation_id_var.get(),
        "trace_id": trace_id_var.get(),
        "span_id": span_id_var.get(),
        "parent_span_id": parent_span_id_var.get(),
    }
    structlog.contextvars.bound_contextvars = structlog.contextvars.bound_contextvars  # noqa
    try:
        cid = set_correlation_id(correlation_id)
        tid, sid = set_trace_id(trace_id, span_id, parent_span_id)
        yield {"correlation_id": cid, "trace_id": tid, "span_id": sid}
    finally:
        # restore previous context
        structlog.contextvars.clear_contextvars()
        for k, v in saved.items():
            if v is not None:
                structlog.contextvars.bind_contextvars(**{k: v})


def propagate_to_celery_headers(headers: dict | None = None) -> dict:
    """Build Celery ``headers`` so a worker can re-hydrate the same context.

    Example::

        task.apply_async(args=[...], headers=propagate_to_celery_headers())
    """
    out = dict(headers or {})
    cid = correlation_id_var.get()
    tid = trace_id_var.get()
    sid = span_id_var.get()
    pid = parent_span_id_var.get()
    if cid:
        out["correlation_id"] = cid
        out["request_id"] = cid
    if tid:
        out["trace_id"] = tid
    if sid:
        out["span_id"] = sid
    if pid:
        out["parent_span_id"] = pid
    return out


def rehydrate_from_celery_headers(headers: dict | None) -> None:
    """Worker side: read headers from the parent task and bind them."""
    if not headers:
        set_correlation_id()
        set_trace_id()
        return
    set_correlation_id(headers.get("correlation_id"))
    set_trace_id(
        trace_id=headers.get("trace_id"),
        span_id=headers.get("span_id"),
        parent_span_id=headers.get("parent_span_id"),
    )