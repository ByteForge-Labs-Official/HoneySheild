"""Liveness + readiness."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.health import aggregate_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Process liveness")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/ready", summary="Dependency readiness")
async def ready() -> dict:
    return await aggregate_health()