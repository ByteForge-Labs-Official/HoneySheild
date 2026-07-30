"""Field-reference helpers used by the formatter and the README."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

# ---------------------------------------------------------------------------
# Envelope fields
# ---------------------------------------------------------------------------
ENVELOPE_FIELDS: Final[tuple[str, ...]] = (
    "timestamp",      # UTC ISO-8601 with ms precision
    "level",          # debug | info | warning | error | critical
    "logger",         # fully-qualified logger name
    "event",          # stable event name (kebab-case verb)
    "app",            # APP_NAME
    "env",            # APP_ENV (development|staging|production)
    "version",        # APP_VERSION
    "pid",            # process id
    "hostname",       # container / pod name
    "thread",         # originating thread name
)

# ---------------------------------------------------------------------------
# Correlation / tracing
# ---------------------------------------------------------------------------
CORRELATION_FIELDS: Final[tuple[str, ...]] = (
    "correlation_id", # request-level UUID4
    "request_id",     # legacy alias of correlation_id
    "trace_id",       # W3C trace-context
    "span_id",
    "parent_span_id",
)

# ---------------------------------------------------------------------------
# Request context (HTTP only)
# ---------------------------------------------------------------------------
REQUEST_FIELDS: Final[tuple[str, ...]] = (
    "method", "path", "route", "status_code", "client_ip",
    "user_agent", "duration_ms", "content_length",
)

# ---------------------------------------------------------------------------
# Auth context
# ---------------------------------------------------------------------------
AUTH_FIELDS: Final[tuple[str, ...]] = (
    "user_id", "username", "user_role",
)

# ---------------------------------------------------------------------------
# Domain (honeypet / IDS / AI)
# ---------------------------------------------------------------------------
DOMAIN_FIELDS: Final[tuple[str, ...]] = (
    "honeypot_id", "honeypot_name", "protocol",
    "source_ip", "source_port", "destination_port",
    "country", "city",
    "severity",
    "mitre_tags",
)

# ---------------------------------------------------------------------------
# Celery / worker
# ---------------------------------------------------------------------------
WORKER_FIELDS: Final[tuple[str, ...]] = (
    "task_id", "task_name", "queue", "worker",
)

# Keys whose values must NEVER leave the formatter unscrubbed.
SENSITIVE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "password", "passwd", "secret", "api_key", "apikey",
        "token", "access_token", "refresh_token", "bearer",
        "authorization", "cookie", "set-cookie", "client_secret",
        "private_key", "jwt",
    }
)


@dataclass(frozen=True, slots=True)
class LogField:
    """Documentation record for one log field (used by the README generator)."""

    name: str
    type: str
    origin: str
    description: str


def all_documented_fields() -> list[LogField]:
    """Return every documented field as `LogField` records."""
    docs: list[LogField] = [
        LogField("timestamp", "string (ISO-8601)", "TimeStamper",
                 "UTC ISO-8601 timestamp with millisecond precision."),
        LogField("level", "string", "add_log_level",
                 "One of debug, info, warning, error, critical."),
        LogField("logger", "string", "add_logger_name",
                 "Fully-qualified logger name (e.g. app.services.auth)."),
        LogField("event", "string", "caller",
                 "Stable kebab-case event name (attack.ingest, auth.login.failed)."),
        LogField("app", "string", "env", "APP_NAME — used to filter multi-tenant logs."),
        LogField("env", "string", "env", "APP_ENV — development / staging / production."),
        LogField("version", "string", "env", "App version (semver)."),
        LogField("pid", "int", "os.getpid", "Process id; combine with hostname for worker key."),
        LogField("hostname", "string", "socket.gethostname", "Container / pod name."),
        LogField("thread", "string", "threading", "Originating thread name."),
        LogField("correlation_id", "string (UUID4)", "middleware",
                 "Per-request id, propagated to async tasks spawned by the request."),
        LogField("request_id", "string (UUID4)", "middleware",
                 "Legacy alias of correlation_id."),
        LogField("trace_id", "string (32-hex)", "middleware",
                 "W3C trace-context id."),
        LogField("span_id", "string (16-hex)", "middleware", "Active span id."),
        LogField("parent_span_id", "string (16-hex)", "middleware", "Parent span id, if any."),
        LogField("method", "string", "http", "HTTP method."),
        LogField("path", "string", "http", "Path template (e.g. /api/v1/attacks/{id})."),
        LogField("route", "string", "http", "Matched route name."),
        LogField("status_code", "int", "http", "Response status code."),
        LogField("client_ip", "string", "http",
                 "Source IP, honouring X-Forwarded-For from trusted proxies only."),
        LogField("user_agent", "string", "http", "Truncated user agent."),
        LogField("duration_ms", "float", "http", "Wall-clock duration of the request."),
        LogField("content_length", "int", "http", "Response size in bytes."),
        LogField("user_id", "string", "auth", "Authenticated user UUID."),
        LogField("username", "string", "auth", "Username."),
        LogField("user_role", "string", "auth", "One of admin / analyst / viewer."),
        LogField("honeypot_id", "string", "domain", "UUID of the bait container."),
        LogField("honeypot_name", "string", "domain",
                 "cowrie, dionaea, mqtt-bait, …"),
        LogField("protocol", "string", "domain", "ssh, telnet, http, rtsp, mqtt, …"),
        LogField("source_ip", "string", "domain", "Attacker IP."),
        LogField("source_port", "int", "domain", "Ephemeral port."),
        LogField("destination_port", "int", "domain", "Bait port."),
        LogField("country", "string", "domain", "GeoIP country code."),
        LogField("city", "string", "domain", "GeoIP city."),
        LogField("severity", "string", "domain", "low / medium / high / critical."),
        LogField("mitre_tags", "list[string]", "domain",
                 "MITRE ATT&CK techniques."),
        LogField("exception", "dict", "exception",
                 "Structlog-rendered traceback with type/value/traceback."),
        LogField("exc_type", "string", "exception", "Exception class name."),
        LogField("exc_message", "string", "exception", "str(exception)."),
        LogField("task_id", "string", "worker", "Celery task UUID."),
        LogField("task_name", "string", "worker", "Fully-qualified task path."),
        LogField("queue", "string", "worker", "Celery queue name."),
        LogField("worker", "string", "worker", "Worker hostname (celery@host)."),
    ]
    return docs


def is_sensitive(key: str) -> bool:
    """Return True if the field name is one we auto-redact."""
    k = key.lower()
    if k in SENSITIVE_KEYS:
        return True
    return any(token in k for token in ("password", "secret", "token", "api_key"))


def filter_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact values for sensitive keys."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if is_sensitive(k):
            out[k] = "***"
        elif isinstance(v, dict):
            out[k] = filter_dict(v)
        else:
            out[k] = v
    return out