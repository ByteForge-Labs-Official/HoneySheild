"""Custom Prometheus metric definitions for the Honeynet backend.

All metrics live under the ``honeynet_`` prefix.  Field-by-field
documentation is kept inline so ``promtool check metrics`` style tooling
isn't required — every metric exists for a clear reason.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# ----------------------------------------------------------------------------
# Local registry — decoupled from the default global so tests can spin up
# isolated FastAPI apps without leaking metrics across test cases.
# ----------------------------------------------------------------------------
REGISTRY = CollectorRegistry()

# ---------------------------------------------------------------------------
# Ingest pipeline (honeypot events → backend → DB)
# ---------------------------------------------------------------------------

honeynet_events_ingested_total = Counter(
    "honeynet_events_ingested_total",
    "Honeypot events successfully persisted to the canonical store.",
    labelnames=("honeypot", "protocol", "severity"),
    registry=REGISTRY,
)

honeynet_events_rejected_total = Counter(
    "honeynet_events_rejected_total",
    "Honeypot events the ingest pipeline rejected (validation, size, auth).",
    labelnames=("honeypot", "reason"),
    registry=REGISTRY,
)

honeynet_event_ingest_duration_seconds = Histogram(
    "honeynet_event_ingest_duration_seconds",
    "Wall-clock time the backend spent ingesting a single honeypot event.",
    labelnames=("honeypot", "protocol"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# AI enrichment (pluggable providers in app/integrations/ai)
# ---------------------------------------------------------------------------

honeynet_ai_insights_total = Counter(
    "honeynet_ai_insights_total",
    "AI-generated insights produced for ingested events.",
    labelnames=("provider", "status"),  # status: success | error | skipped
    registry=REGISTRY,
)

honeynet_ai_request_duration_seconds = Histogram(
    "honeynet_ai_request_duration_seconds",
    "Latency of upstream AI provider calls.",
    labelnames=("provider",),
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
    registry=REGISTRY,
)

honeynet_ai_tokens_total = Counter(
    "honeynet_ai_tokens_total",
    "Tokens billed by upstream AI providers (prompt + completion).",
    labelnames=("provider", "kind"),  # kind: prompt | completion
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Celery workers
# ---------------------------------------------------------------------------

honeynet_celery_tasks_total = Counter(
    "honeynet_celery_tasks_total",
    "Celery task outcomes by task name.",
    labelnames=("task", "status"),  # status: success | failure | retry
    registry=REGISTRY,
)

honeynet_celery_task_duration_seconds = Histogram(
    "honeynet_celery_task_duration_seconds",
    "End-to-end duration of Celery tasks (queue time + execution).",
    labelnames=("task",),
    buckets=(0.05, 0.1, 0.5, 1, 5, 10, 30, 60, 300),
    registry=REGISTRY,
)

honeynet_celery_queue_depth = Gauge(
    "honeynet_celery_queue_depth",
    "Tasks pending in each Celery queue (sampled at scrape time).",
    labelnames=("queue",),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# IDS feeds (Suricata + Zeek → backend)
# ---------------------------------------------------------------------------

honeynet_ids_alerts_total = Counter(
    "honeynet_ids_alerts_total",
    "IDS alerts relayed into the platform from Suricata / Zeek.",
    labelnames=("engine", "severity"),  # engine: suricata | zeek
    registry=REGISTRY,
)

honeynet_ids_last_event_timestamp = Gauge(
    "honeynet_ids_last_event_timestamp",
    "Unix timestamp of the most recent IDS event ingested per engine.",
    labelnames=("engine",),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Database / cache health (cheap, polling-free gauges)
# ---------------------------------------------------------------------------

honeynet_db_pool_connections = Gauge(
    "honeynet_db_pool_connections",
    "SQLAlchemy connection-pool gauges for the primary DB.",
    labelnames=("pool", "state"),  # state: idle | checked_out | overflow
    registry=REGISTRY,
)

honeynet_db_locks_held = Gauge(
    "honeynet_db_locks_held",
    "Active Postgres advisory locks held by the application.",
    labelnames=("name",),
    registry=REGISTRY,
)

honeynet_redis_up = Gauge(
    "honeynet_redis_up",
    "1 if Redis is reachable from the app's last probe, else 0.",
    registry=REGISTRY,
)

honeynet_redis_pubsub_subscribers = Gauge(
    "honeynet_redis_pubsub_subscribers",
    "Active Redis Pub/Sub subscribers registered by the app.",
    labelnames=("channel",),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Application-level (live status of long-running internals)
# ---------------------------------------------------------------------------

honeynet_app_dependency_up = Gauge(
    "honeynet_app_dependency_up",
    "1 if a critical dependency is reachable, else 0.",
    labelnames=("dependency",),  # postgres / redis / mqtt-broker / elasticsearch
    registry=REGISTRY,
)

honeynet_app_active_websockets = Gauge(
    "honeynet_app_active_websockets",
    "Active WebSocket connections (e.g. dashboard /api/v1/ws).",
    labelnames=("endpoint",),
    registry=REGISTRY,
)

honeynet_app_exception_total = Counter(
    "honeynet_app_exception_total",
    "Unhandled exceptions raised by request handlers.",
    labelnames=("type", "path"),
    registry=REGISTRY,
)
