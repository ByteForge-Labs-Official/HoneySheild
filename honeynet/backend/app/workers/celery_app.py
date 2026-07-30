"""Celery application factory."""
from __future__ import annotations

from celery import Celery

from app.core.config.constants import (
    QUEUE_ANALYZE,
    QUEUE_DEFAULT,
    QUEUE_INGEST,
)
from app.core.config.settings import get_settings

_settings = get_settings()

celery_app = Celery(
    "honeynet",
    broker=str(_settings.redis_dsn),
    backend=str(_settings.redis_dsn),
    include=[
        "app.workers.tasks.ingest",
        "app.workers.tasks.analyze",
        "app.workers.tasks.maintenance",
    ],
)

celery_app.conf.update(
    task_default_queue=QUEUE_DEFAULT,
    task_queues={
        QUEUE_DEFAULT: {"routing_key": QUEUE_DEFAULT},
        QUEUE_INGEST:  {"routing_key": QUEUE_INGEST},
        QUEUE_ANALYZE: {"routing_key": QUEUE_ANALYZE},
    },
    task_routes={
        "app.workers.tasks.ingest.*":      {"queue": QUEUE_INGEST},
        "app.workers.tasks.analyze.*":     {"queue": QUEUE_ANALYZE},
        "app.workers.tasks.maintenance.*": {"queue": QUEUE_DEFAULT},
    },
    worker_send_task_events=True,
    task_send_sent_event=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
)