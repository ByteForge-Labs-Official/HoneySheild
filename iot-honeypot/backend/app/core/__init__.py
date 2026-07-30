"""app.core.monitoring

Single entry point for *application-side* observability in the Honeynet
backend.  This package wires:

* `prometheus-fastapi-instrumentator` to export the default Python / HTTP
  metrics at ``GET /api/v1/metrics``,
* `app.core.monitoring.collectors` — domain-specific counters, histograms
  and gauges for ingest, AI, Celery, IDS feeds, and the underlying
  Postgres / Redis connections,
* `app.core.monitoring.health` — liveness (process) and readiness
  (dependency-aware) checks exposed via ``GET /api/v1/health`` and
  ``GET /api/v1/ready``.

Design notes:

* Importing this package is **side-effect-free**.  Call
  ``install_monitoring(app)`` once during startup (see ``app.main``) and
  it will register the router, instrument the FastAPI app and ensure all
  custom collectors are initialised.
* All metrics live in the ``honeynet_`` namespace so they never collide
  with the defaults exported by ``prometheus-fastapi-instrumentator``
  (which use ``http_*`` / ``process_*`` / ``python_*``).
* Cardinality is kept low — labels that can grow unbounded (raw IP
  addresses, user names) are **never** used as metric labels.
"""

from app.core.monitoring.install import install_monitoring
from app.core.monitoring.metrics import REGISTRY as METRICS_REGISTRY

__all__ = ["install_monitoring", "METRICS_REGISTRY"]
