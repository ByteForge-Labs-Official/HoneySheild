"""Celery application factory."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

_s = get_settings()

celery_app = Celery(
    "honeynet",
    broker=str(_s.celery_broker_url),
    backend=str(_s.celery_result_backend),
    include=[
        "app.workers.tasks.ai_tasks",
        "app.workers.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "enrich-events-with-ai": {
        "task": "app.workers.tasks.ai_tasks.enrich_pending_events",
        "schedule": crontab(minute="*/5"),
    },
    "rotate-stale-sessions": {
        "task": "app.workers.tasks.maintenance_tasks.rotate_stale_sessions",
        "schedule": crontab(minute="*/15"),
    },
}