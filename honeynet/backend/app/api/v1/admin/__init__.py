"""admin subrouter."""
from app.api.v1.admin.routes import router

__all__ = ["router"]


def init_router(): return router