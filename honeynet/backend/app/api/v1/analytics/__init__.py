"""analytics subrouter."""
from app.api.v1.analytics.routes import router

__all__ = ["router"]


def init_router(): return router