"""health subrouter."""
from app.api.v1.health.routes import router

__all__ = ["router"]


def init_router() -> "APIRouter":
    return router