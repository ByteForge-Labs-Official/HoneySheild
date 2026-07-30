"""Celery task metrics — both worker-side and producer-side observations."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from app.core.monitoring.metrics import (
    honeynet_celery_queue_depth,
    honeynet_celery_task_duration_seconds,
    honeynet_celery_tasks_total,
)


def init() -> None:
    honeynet_celery_tasks_total.labels(task="-", status="-").inc(0)


def observe(task: str, status: str) -> None:
    honeynet_celery_tasks_total.labels(task=task, status=status).inc()


@contextmanager
def time_task(task: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        honeynet_celery_task_duration_seconds.labels(task=task).observe(
            time.perf_counter() - start
        )


def set_queue_depth(queue: str, depth: int) -> None:
    honeynet_celery_queue_depth.labels(queue=queue).set(depth)
