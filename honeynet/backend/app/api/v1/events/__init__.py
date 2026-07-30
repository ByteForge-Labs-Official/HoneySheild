"""events subrouter."""
from app.api.v1.events.routes import router

__all__ = ["router"]


def init_router(): return router