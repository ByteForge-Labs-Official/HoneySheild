# 🪵 Centralized Logging

This module is the single source of truth for **observability** in the IoT Honeynet
Research Platform. Every event — HTTP request, broker connection, attack ingest,
AI enrichment, Celery task, exception — passes through one of the loggers created
here, carrying a consistent set of fields regardless of where it was emitted.

> **Stack:** `structlog` (typed, structured events) bridging into the stdlib
> `logging` package so we can re-use `logging.Handler` subclasses (rotating files,
> database sinks, Sentry, etc.).

---

## 🎯 Why logging is important

| Reason | What it gives us |
|---|---|
| **Incident response** | A timeline of what an attacker (or a buggy deploy) actually did. |
| **Compliance** | Tamper-evident audit trail of operator actions on the honeypot. |
| **Performance** | Slow-request traces, DB query timing, MQTT round-trip latency. |
| **Cross-service correlation** | Trace a single TCP probe from edge → honeypot → IDS → Postgres. |
| **Audit** | Reconstruct which operator dismissed which alert at what time. |
| **Operational health** | Feed ELK / Loki / Datadog the same JSON wire-format. |

In a honeypet platform especially: **attacker activity is the product.** Losing logs
is the same as losing the data we are paid to study.

---

## 🧱 Architectural pieces

```
                    ┌────────────────────────────────────┐
                    │      application code              │
                    │   log.info("attack.ingest", …)     │
                    └────────────────┬───────────────────┘
                                     │  structlog-bound logger
                                     ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ structlog pipeline (processors)                             │
   │  ① contextvars merge    → correlation_id, trace_id, user_id │
   │  ② add_logger_name     → logger=app.services.auth           │
   │  ③ add_log_level       → level=info                         │
   │  ④ TimeStamper         → timestamp=2026-07-28T10:11:12Z     │
   │  ⑤ StackInfoRenderer   → callsite when stack=True           │
   │ ⑥ format_exc_info     → exception field (traceback)        │
   │  ⑦ scrub_secrets       → keys in {password,token,…}=***     │
   │  ⑧ PiiHasher           → user.email → user_email_hash       │
   │  ⑨ EventNormalizer     → coerce datetime/UUID/Decimal       │
   └────────────────┬────────────────────────────────────────────┘
                    │   ProcessorFormatter
                    ▼
   ┌──────────────────────────┬──────────────────┬────────────────┐
   │   ConsoleHandler         │ RotatingFile     │  DbHandler     │
   │   (stdout, colored/JSON) │  handler         │  (audit_log)   │
   └──────────────────────────┴──────────────────┴────────────────┘
                    │              │              │
                    ▼              ▼              ▼
              your terminal   /data/logs/     PostgreSQL
                              honeynet.log    app_log rows
                              + rotated .1..N
```

---

## ✅ Key concepts

### Structured logging
The unit of log is a **key/value event dict**, not a free-form string:

```python
log.info("attack.ingest", source_ip="1.2.3.4", protocol="ssh", severity="high")
# →  {"event":"attack.ingest","source_ip":"1.2.3.4","protocol":"ssh","severity":"high", ...}
```

This makes events machine-queryable: `level:error AND logger:auth_service` or
`source_country:CN AND severity:critical` become trivial Kibana queries.

### JSON logging
In any non-dev environment we emit **one JSON object per line**. Every record has
the same envelope so a Loki / ELK / Datadog ingestion pipeline can rely on it
without per-service schemas. The renderer used is `structlog.processors.JSONRenderer`.

### Log rotation
File logs are written through `logging.handlers.RotatingFileHandler` with
`maxBytes = LOG_ROTATION_MAX_BYTES` and `backupCount = LOG_ROTATION_BACKUP_COUNT`.
On overflow the active file is renamed `honeynet.log.1`, `.2`, … and a new
`honeynet.log` is opened. Old files become eligible for deletion by the
retention reaper (see below).

### Log retention
A periodic Celery beat task (`app.workers.tasks.maintenance_tasks.purge_old_logs`)
enumerates the rotated files, removes anything older than `LOG_RETENTION_DAYS`,
and emits a `log.retention` audit event. The DB sink can also be partitioned by
date — see `app/db/models/audit_log.py`.

### Correlation IDs
Every incoming HTTP request is tagged with a **`correlation_id`** (UUID4) taken
from the inbound `X-Correlation-ID` header when present, otherwise freshly
generated. The ID is bound into `structlog.contextvars` for the lifetime of the
request, so every log line — including Celery tasks spawned from that request —
carries the same value, letting us assemble a full request trace.

### Trace IDs
For distributed tracing we accept an OpenTelemetry-compatible **`trace_id`**
(32-hex) and **`span_id`** (16-hex) from the inbound `traceparent` header
(W3C Trace Context). When none is present we generate one. Both are emitted on
every log record, side-by-side with the `correlation_id`.

### Log levels
We expose the standard levels with the following policy:

| Level     | Use | Local console | JSON | File | DB |
|-----------|-----|---------------|------|------|----|
| DEBUG     | debugging detail | ✓ | – | ✓ | – |
| INFO      | normal lifecycle (`http.request.start`, `attack.ingest`) | ✓ | ✓ | ✓ | – |
| WARNING   | recoverable issue, slow query, retry | ✓ | ✓ | ✓ | ✓ |
| ERROR     | caught exception that the caller should know about | ✓ | ✓ | ✓ | ✓ |
| CRITICAL  | unrecoverable — page the on-call | ✓ | ✓ | ✓ | ✓ |

### Log aggregation
In production, logs are expected to flow into an aggregator (Loki / ELK /
Vector → OpenSearch). The Docker compose stack ships a `loki` + `promtail`
profile and a Filebeat → Logstash → Elasticsearch pipeline (see
`deploy/docker-compose.yml` and `ids/`).

---

## 📚 Every field, explained

The `LogRecord` produced by the formatter always includes the **envelope**
fields, and may include **context**, **domain**, and **exception** fields
depending on what your call site bound.

### 📨 Envelope (always present)

| Field          | Type              | Origin | Description |
|----------------|-------------------|--------|-------------|
| `timestamp`    | string (ISO-8601) | TimeStamper | UTC ISO-8601 timestamp with millisecond precision (`2026-07-28T10:11:12.842Z`). |
| `level`        | string            | add_log_level | One of `debug`, `info`, `warning`, `error`, `critical`. |
| `logger`       | string            | add_logger_name | The Python logger name; usually the fully-qualified module path (`app.services.auth`). |
| `event`        | string            | caller | The event name (kebab-case verb). Acts as a stable, machine-readable discriminator: `attack.ingest`, `auth.login.failed`. |
| `app`          | string            | env | `APP_NAME` from settings — used to filter multi-tenant logs. |
| `env`          | string            | env | `APP_ENV` — `development` / `staging` / `production`. |
| `version`      | string            | env | App version (semver). Useful when correlating bug reports. |
| `pid`          | int               | os.getpid | Process id. Increases rapidly under multi-worker Gunicorn — use `hostname`+`pid` as a unique key per worker. |
| `hostname`     | string            | socket.gethostname | Container / pod name. |
| `thread`       | string            | threading | Originating thread name (gunicorn worker, mqtt-loop, etc.). |

### 🔗 Correlation & tracing (always present after middleware)

| Field            | Type   | Description |
|------------------|--------|-------------|
| `correlation_id` | string (UUID4) | Per-request ID. Propagated to async tasks spawned by the request. Reproduces the user-facing transaction. |
| `request_id`     | string (UUID4) | Alias of `correlation_id` kept for backwards-compat with older dashboards. |
| `trace_id`       | string (32-hex) | OpenTelemetry trace id. |
| `span_id`        | string (16-hex) | Active span id. |
| `parent_span_id` | string (16-hex) | Parent span id, if any. |

### 🌐 Request context (HTTP only)

| Field            | Type | Description |
|------------------|------|-------------|
| `method`         | string | HTTP method. |
| `path`           | string | Path template (e.g. `/api/v1/attacks/{id}`) — not the rendered URL. |
| `route`          | string | Matched route name. |
| `status_code`    | int   | Response status. |
| `client_ip`      | string | Source IP, honouring `X-Forwarded-For` from trusted proxies only. |
| `user_agent`     | string | Truncated user agent. |
| `duration_ms`    | float | Wall-clock duration of the request. |
| `content_length` | int   | Response size in bytes. |

### 👤 Auth context (after `require_auth`)

| Field        | Type   | Description |
|--------------|--------|-------------|
| `user_id`    | string | UUID of the authenticated user. |
| `username`   | string | Username. |
| `user_role`  | string | One of `admin` / `analyst` / `viewer`. |

### 🛡️ Domain — honeypet / IDS / AI

| Field             | Type   | Description |
|-------------------|--------|-------------|
| `honeypot_id`     | string | UUID of the bait container. |
| `honeypot_name`   | string | `cowrie`, `dionaea`, `mqtt-bait`, etc. |
| `protocol`        | string | `ssh`, `telnet`, `http`, `rtsp`, `mqtt`, `modbus`, `upnp`. |
| `source_ip`       | string | Attacker IP. |
| `source_port`     | int    | Ephemeral port. |
| `destination_port`| int    | Bait port. |
| `country`         | string | GeoIP country code. |
| `city`            | string | GeoIP city. |
| `severity`        | string | `low` / `medium` / `high` / `critical`. |
| `mitre_tags`      | list   | MITRE ATT&CK techniques (`["T1110","T1059"]`). |

### 🧨 Exception (`level in {error, critical}`)

| Field         | Type   | Description |
|---------------|--------|-------------|
| `exception`   | dict   | Structlog-rendered traceback (`exc_info=True`). Contains `type`, `value`, `traceback` (list of frames). |
| `exc_type`    | string | Exception class name. |
| `exc_message` | string | `str(exception)`. Useful when `exc_info` is false. |

### 🧪 Celery / worker

| Field            | Type   | Description |
|------------------|--------|-------------|
| `task_id`        | string | Celery task UUID. |
| `task_name`      | string | Fully-qualified task (`app.workers.tasks.ai.enrich_pending_events`). |
| `queue`          | string | Celery queue name. |
| `worker`         | string | Worker hostname (`celery@<hostname>`). |

---

## 🚀 Public API

```python
from app.core.logging import configure_logging, get_logger, set_correlation_id

configure_logging()                        # call once in main.py
log = get_logger(__name__)
log.info("attack.ingest", source_ip="1.2.3.4", protocol="ssh", severity="critical")

with correlation_scope(correlation_id="abc-123"):
    log.warning("rate.limit.exceeded")     # both tags attached
```

### Functions

| Function | Purpose |
|---|---|
| `configure_logging(level=, json=, file_path=, etc.)` | Idempotently initialise the entire pipeline. Called from `app/main.py:lifespan`. |
| `get_logger(name=None, **bind)` | Returns a bound structlog logger. Pre-bound context (`app`, `env`, …) is added automatically. |
| `set_correlation_id(value)` | Bind `correlation_id` into contextvars for the current async task/request. |
| `set_trace_id(trace_id, span_id=None)` | Bind W3C trace-context fields. |
| `bind_context(**kv)` / `clear_context()` | Manipulate the request-scoped context. |
| `log_exception(exc, **extra)` | Format an exception into the `exception` field with optional context. |
| `@timed("operation.name")` | Decorator that emits `operation.duration_ms` events. |

### Sinks

| Handler | Class | Output |
|---|---|---|
| Console | `RichConsoleHandler` (dev) / `JsonStreamHandler` (prod) | stdout |
| File    | `RotatingFileHandler` (stdlib) | `LOG_DIR/<APP_NAME>.log` with `.1`..`.N` rotation |
| Database| `DbLogHandler` (async) | `audit_log` table (WARNING+) |
| Syslog  | optional | `LOG_SYSLOG_HOST:LOG_SYSLOG_PORT` |

---

## 🔐 PII / secret scrubbing

The `scrub_secrets` processor strips well-known sensitive keys (`password`,
`token`, `authorization`, `cookie`, `client_secret`, …) before any handler
sees them. Field values become `***`. Add new keys in `SENSITIVE_KEYS`.

We do **not** log raw request bodies or authorization headers — only
`method`, `path`, `status_code`, `duration_ms`, `client_ip`, `user_agent`,
and the parsed route params.

---

## 🔌 Plugging in your own handler

Drop any `logging.Handler` instance into `configure_logging(extra_handlers=[…])`.
A Sentry handler looks like:

```python
import sentry_sdk
from logging.handlers import SysLogHandler

class SentryHandler(logging.Handler):
    def emit(self, record):
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("log_event", record.__dict__)
            sentry_sdk.capture_message(record.getMessage(), level=record.levelname)

configure_logging(extra_handlers=[SentryHandler()])
```

---

## 🔭 What you'll see in production

One line of JSON per request:

```json
{
  "timestamp":"2026-07-28T10:11:12.842Z","level":"info","logger":"app.api.v1.attacks",
  "event":"attack.list","app":"honeynet-api","env":"production","version":"1.0.0",
  "pid":17,"hostname":"honeynet-api-7c8d","thread":"uvicorn",
  "correlation_id":"f6c1…","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id":"00f067aa0ba902b7","method":"GET","path":"/api/v1/attacks","route":"attacks_list",
  "status_code":200,"client_ip":"203.0.113.7","user_agent":"Mozilla/5.0",
  "duration_ms":27.4,"user_id":"…","username":"analyst","user_role":"analyst"
}
```

That's the entire checklist: structure, JSON, rotation, retention, correlation,
trace, level, aggregation.
