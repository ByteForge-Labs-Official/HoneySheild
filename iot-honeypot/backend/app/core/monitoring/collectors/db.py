"""Database / cache gauges — refreshed by ``app.core.monitoring.health.readiness``."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.monitoring.metrics import (
    honeynet_db_locks_held,
    honeynet_db_pool_connections,
    honeynet_redis_pubsub_subscribers,
    honeynet_redis_up,
)


def init() -> None:
    # Pre-create labels to avoid empty-scrape warnings on first boot.
    honeynet_db_pool_connections.labels(pool="primary", state="idle").set(0)
    honeynet_db_pool_connections.labels(pool="primary", state="checked_out").set(0)
    honeynet_db_pool_connections.labels(pool="primary", state="overflow").set(0)
    honeynet_redis_up.set(0)


async def refresh_pool_gauge(engine: AsyncEngine, pool_name: str = "primary") -> None:
    """Sample SQLAlchemy pool depth — cheap, called by readiness probe."""
    pool = engine.sync_engine.pool  # type: ignore[attr-defined]
    honeynet_db_pool_connections.labels(pool=pool_name, state="idle").set(pool.checkedin())
    honeynet_db_pool_connections.labels(pool=pool_name, state="checked_out").set(pool.checkedout())
    honeynet_db_pool_connections.labels(pool=pool_name, state="overflow").set(pool.overflow())


def mark_lock(name: str, held: bool) -> None:
    honeynet_db_locks_held.labels(name=name).set(1 if held else 0)


def mark_redis_up(up: bool) -> None:
    honeynet_redis_up.set(1 if up else 0)


def set_redis_subscribers(channel: str, count: int) -> None:
    honeynet_redis_pubsub_subscribers.labels(channel=channel).set(count)
