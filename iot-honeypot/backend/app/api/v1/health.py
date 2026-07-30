"""Health endpoints: liveness + readiness + version banner."""
from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.schemas.common import HealthOut
from app.services.health import aggregate_health

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthOut, summary="Liveness probe")
async def health() -> HealthOut:
    """Cheap check; always 200 unless the process is broken."""
    return HealthOut(status="ok", version=settings.app_version)


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict:
    """Verifies dependencies (Postgres, Redis) are reachable."""
    components = await aggregate_health()
    healthy = all(v == "ok" for k, v in components.items() if k in {"db", "redis"})
    return {
        "status": "ok" if healthy else "degraded",
        "components": components,
    }


@router.get("/version", summary="Build info")
async def version() -> dict:
    return {"name": settings.app_name, "version": settings.app_version, "env": settings.app_env}