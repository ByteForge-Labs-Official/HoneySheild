"""auth subrouter."""
from app.api.v1.auth.routes import router

__all__ = ["router"]


def init_router(): return router