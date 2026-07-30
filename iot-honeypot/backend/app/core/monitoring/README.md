# app.core.monitoring

Application-side observability for the Honeynet backend.

| Concern | Module | Purpose |
|---|---|---|
| Process liveness       | `health.liveness`    | `GET /api/v1/health`  — does the interpreter respond? |
| Dependency readiness   | `health.readiness`   | `GET /api/v1/ready`   — are Postgres / Redis / MQTT reachable? |
| HTTP + process metrics | `install.Instrumentator` | `GET /api/v1/metrics` — Prometheus exposition |
| Honeypot ingest        | `collectors.ingest`  | counters, histogram (latency) + rejection reasons |
| AI enrichment          | `collectors.ai`      | provider outcomes, latency, token usage |
| Celery workers         | `collectors.celery`  | task outcomes, durations, queue depth |
| IDS feeders            | `collectors.ids`     | Suricata / Zeek alert counters |
| Database / cache       | `collectors.db`      | pool depth, advisory locks, Redis pubsub fan-out |
| App internals          | `collectors.app`     | dependency up, WS counts, unhandled exceptions |

## Wiring

In `app/main.py`:

```python
from app.core.monitoring import install_monitoring

def create_app() -> FastAPI:
    app = FastAPI(...)
    install_monitoring(app)
    return app
```

That's the whole interface.  `install_monitoring` mounts the metrics
and health routers and bootstraps every collector in the right order.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health`  | Liveness, 200 unless the process is deadlocked |
| GET | `/api/v1/ready`   | Readiness, 200 when required deps are healthy |
| GET | `/api/v1/metrics` | Prometheus text-format exposition |

## Metric catalogue

All metrics live under the `honeynet_` prefix.  See
`metrics.py` for the authoritative list; the readme in
`observability/README.md` documents each field in detail.

## Cardinality rules

* Never label a metric with raw IP addresses, full request bodies or
  user names.
* Prefer enumerated, low-cardinality labels (`protocol` ∈ {ssh, telnet,
  http, …}, `severity` ∈ {low, med, high, critical}).
* Use buckets that make sense for the operation (latencies for AI
  queries span seconds, not microseconds).

## Health-check contract

| Code | When |
|------|------|
| 200 — `/health` | Process up |
| 200 — `/ready`  | Postgres & Redis reachable |
| 503 — `/ready`  | A required dependency probe failed |
| 5xx — `/health` | Process wedged (handled by container restart policy) |

The endpoint returns JSON so dashboards can build rich status widgets
without parsing strings.
