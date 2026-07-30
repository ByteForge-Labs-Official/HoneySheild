"""attacks subrouter."""
from app.api.v1.attacks.routes import router

__all__ = ["router"]


def init_router(): return router