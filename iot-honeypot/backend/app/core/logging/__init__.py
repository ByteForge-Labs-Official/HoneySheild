"""Public surface of the logging module."""
from app.core.logging.config import (
    configure_logging,
    get_db_handler,
    is_configured,
)
from app.core.logging.context import (
    bind_context,
    clear_context,
    correlation_scope,
    current_correlation_id,
    current_trace_id,
    new_correlation_id,
    new_span_id,
    new_trace_id,
    propagate_to_celery_headers,
    rehydrate_from_celery_headers,
    set_correlation_id,
    set_trace_id,
)
from app.core.logging.exception_logger import log_exception
from app.core.logging.factory import get_logger
from app.core.logging.middleware import (
    CorrelationIdMiddleware,
    configure_trusted_proxies,
)

__all__ = [
    # bootstrap
    "configure_logging",
    "is_configured",
    "get_db_handler",
    # logger
    "get_logger",
    "log_exception",
    # context
    "bind_context",
    "clear_context",
    "correlation_scope",
    "current_correlation_id",
    "current_trace_id",
    "new_correlation_id",
    "new_span_id",
    "new_trace_id",
    "set_correlation_id",
    "set_trace_id",
    "propagate_to_celery_headers",
    "rehydrate_from_celery_headers",
    # middleware
    "CorrelationIdMiddleware",
    "configure_trusted_proxies",
]