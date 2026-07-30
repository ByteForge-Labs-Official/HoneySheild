"""threats subrouter."""
from app.api.v1.threats.routes import router

__all__ = ["router"]


def init_router(): return router