"""devices subrouter."""
from app.api.v1.devices.routes import router

__all__ = ["router"]


def init_router(): return router