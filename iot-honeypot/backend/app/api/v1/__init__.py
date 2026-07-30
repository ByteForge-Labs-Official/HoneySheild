"""v1 API aggregator: combines every v1 subrouter."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, honeypots, alerts, events, ai, health

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(honeypots.router, prefix="/honeypots", tags=["honeypots"])
api_v1_router.include_router(events.router, prefix="/events", tags=["events"])
api_v1_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_v1_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_v1_router.include_router(health.router, tags=["health"])