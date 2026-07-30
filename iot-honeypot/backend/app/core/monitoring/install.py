"""Wiring layer between FastAPI and the monitoring subsystem.

Called once from ``app.main.create_app``.  Doing it in a dedicated module
keeps ``main.py`` free of observability detail and makes the side-effects
easy to test.
"""

from __future__ import annotations

import logging
from typing import Final

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.monitoring.collectors import (
    ai as ai_collector,
    app as app_collector,
    celery as celery_collector,
    db as db_collector,
    ids as ids_collector,
    ingest as ingest_collector,
)
from app.core.monitoring.health import router as health_router
from app.core.monitoring.metrics import REGISTRY

_LOG = logging.getLogger(__name__)

_METRICS_PATH: Final[str] = "/api/v1/metrics"
_HEALTH_PATH: Final[str] = "/api/v1/health"
_READY_PATH: Final[str] = "/api/v1/ready"


def install_monitoring(app: FastAPI) -> None:
    """Mount metrics, health checks and initialise all custom collectors.

    Order matters: collectors first (so they observe the very first
    request), instrumentator second (so it wraps routes and emits
    http_* metrics), routers last.
    """

    _LOG.info("monitoring.install", extra={"metrics_path": _METRICS_PATH})

    # 1. Domain-specific collectors (counters, gauges, histograms).
    ingest_collector.init()
    ai_collector.init()
    celery_collector.init()
    ids_collector.init()
    db_collector.init()
    app_collector.init()

    # 2. Default Prometheus / FastAPI metrics.
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=[_METRICS_PATH, f"{_HEALTH_PATH}", f"{_READY_PATH}"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
        metrics_registry=REGISTRY,
    ).instrument(app).expose(
        app,
        endpoint=_METRICS_PATH,
        include_in_schema=False,
        should_gzip=True,
    )

    # 3. Health endpoints (liveness + readiness).
    app.include_router(health_router, tags=["health"])

    _LOG.info("monitoring.ready", extra={"registry_size": len(list(REGISTRY.collect()))})
