"""Liveness + readiness endpoints.

Liveness (``/api/v1/health``) — *is this process alive?*
    Returns 200 as long as the Python interpreter is responsive.  Used
    by Kubernetes / Docker to decide whether to restart the container.

Readiness (``/api/v1/ready``) — *can this instance serve traffic?*
    Returns 200 only when all required dependencies (DB, Redis, MQTT)
    are reachable; used by load balancers to gate traffic during
    startup, draining or partial outages.

Both endpoints return a JSON body so dashboards / probes can show rich
status without parsing human-readable strings.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

from app.core.config.settings import get_settings
from app.core.monitoring.collectors import app as app_collector
from app.core.monitoring.collectors import db as db_collector

_LOG = logging.getLogger(__name__)
router = APIRouter()

# Per-dependency timeout (seconds) — keep small so the endpoint stays
# responsive even when something downstream is wedged.
_PROBE_TIMEOUT: float = 1.5


# ---------------------------------------------------------------------------
# Dependency probes
# ---------------------------------------------------------------------------

async def _probe_db(request: Request) -> tuple[bool, str]:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        return False, "engine-not-initialised"
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=_PROBE_TIMEOUT,
            )
        await db_collector.refresh_pool_gauge(engine)
        app_collector.mark_dependency("postgres", True)
        return True, "ok"
    except Exception as exc:  # pragma: no cover
        app_collector.mark_dependency("postgres", False)
        return False, f"{type(exc).__name__}: {exc}"[:200]


async def _probe_redis(request: Request) -> tuple[bool, str]:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return False, "redis-not-initialised"
    try:
        pong = await asyncio.wait_for(redis.ping(), timeout=_PROBE_TIMEOUT)
        ok = bool(pong)
        db_collector.mark_redis_up(ok)
        app_collector.mark_dependency("redis", ok)
        return ok, "pong" if ok else "no-pong"
    except Exception as exc:  # pragma: no cover
        db_collector.mark_redis_up(False)
        app_collector.mark_dependency("redis", False)
        return False, f"{type(exc).__name__}: {exc}"[:200]


async def _probe_mqtt(request: Request) -> tuple[bool, str]:
    bridge = getattr(request.app.state, "mqtt_bridge", None)
    if bridge is None:
        # MQTT is optional — an unconfigured instance still serves UI.
        app_collector.mark_dependency("mqtt_broker", False)
        return True, "disabled"
    try:
        ok = await asyncio.wait_for(bridge.health(), timeout=_PROBE_TIMEOUT)
        app_collector.mark_dependency("mqtt_broker", ok)
        return ok, "ok" if ok else "not-connected"
    except Exception as exc:  # pragma: no cover
        app_collector.mark_dependency("mqtt_broker", False)
        return False, f"{type(exc).__name__}: {exc}"[:200]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", summary="Liveness probe")
async def liveness() -> dict:
    """Process up — does *not* check downstream dependencies."""
    return {
        "status": "ok",
        "service": "honeynet-api",
        "env": get_settings().APP_ENV,
        "uptime_seconds": time.time() - _PROCESS_STARTED_AT,
    }


@router.get("/ready", summary="Readiness probe")
async def readiness(request: Request, response: Response) -> dict:
    """Aggregate readiness checks.  Returns 503 if any *required*
    dependency is unhealthy (Redis + Postgres are required; MQTT is
    best-effort).
    """

    probes: dict[str, Callable[[Request], Awaitable[tuple[bool, str]]]] = {
        "postgres": _probe_db,
        "redis":    _probe_redis,
        "mqtt":     _probe_mqtt,
    }

    results: dict[str, dict] = {}
    overall_ok = True

    # Run probes concurrently but bound the total wait.
    coros = {name: probe(request) for name, probe in probes.items()}
    done = await asyncio.gather(*coros.values(), return_exceptions=True)
    for (name, _), outcome in zip(coros.items(), done):
        if isinstance(outcome, BaseException):
            results[name] = {"ok": False, "error": f"{type(outcome).__name__}"}
            if name in ("postgres", "redis"):
                overall_ok = False
            continue
        ok, detail = outcome  # type: ignore[misc]
        results[name] = {"ok": ok, "detail": detail}
        if name in ("postgres", "redis") and not ok:
            overall_ok = False

    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if overall_ok else "degraded",
        "checks": results,
    }


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

_PROCESS_STARTED_AT: float = time.time()
