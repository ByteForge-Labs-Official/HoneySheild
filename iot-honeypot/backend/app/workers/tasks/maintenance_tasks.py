"""Periodic maintenance tasks."""
from __future__ import annotations

import asyncio

from sqlalchemy import delete

from app.db.session import SessionMaker
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.maintenance_tasks.rotate_stale_sessions")
def rotate_stale_sessions() -> int:
    return asyncio.run(_rotate())


async def _rotate() -> int:
    from app.db.models.user import User  # local import to avoid circular
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
    async with SessionMaker() as session:
        stmt = delete(User).where(User.last_login_at.is_not(None), User.last_login_at < cutoff)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount or 0