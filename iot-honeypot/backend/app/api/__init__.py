"""HTTP API package."""
from app.api.v1 import api_v1_router  # re-exported from app.api.v1.__init__

__all__ = ["api_v1_router"]