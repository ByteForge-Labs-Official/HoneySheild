"""External integrations (Redis, MQTT, IDS)."""
from app.integrations.redis.client import get_redis

__all__ = ["get_redis"]