"""Aggregator for v1 routers + WebSocket endpoints."""
from fastapi import APIRouter

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.devices.routes import router as devices_router
from app.api.v1.attacks.routes import router as attacks_router
from app.api.v1.events.routes import router as events_router
from app.api.v1.analytics.routes import router as analytics_router
from app.api.v1.threats.routes import router as threats_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.health.routes import router as health_router
from app.api.v1.ws.routes import router as ws_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router,  prefix="/health",  tags=["health"])
api_v1_router.include_router(auth_router,    prefix="/auth",    tags=["auth"])
api_v1_router.include_router(users_router,   prefix="/users",   tags=["users"])
api_v1_router.include_router(devices_router, prefix="/devices", tags=["devices"])
api_v1_router.include_router(attacks_router, prefix="/attacks", tags=["attacks"])
api_v1_router.include_router(events_router,  prefix="/events",  tags=["events"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_v1_router.include_router(threats_router, prefix="/threats", tags=["threats"])
api_v1_router.include_router(admin_router,   prefix="/admin",   tags=["admin"])
api_v1_router.include_router(ws_router,      prefix="/ws",      tags=["ws"])
