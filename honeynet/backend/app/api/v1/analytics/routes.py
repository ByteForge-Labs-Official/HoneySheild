"""Dashboard analytics — top IPs, timeline, geo, MITRE cloud."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.services.analytics.aggregator import (
    geo_distribution, mitre_cloud, timeline, top_ips,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-ips")
async def _top_ips(_: CurrentUser, db: DBSession, limit: int = Query(50, le=500)):
    return [t.model_dump() for t in await top_ips(db, limit=limit)]


@router.get("/timeline")
async def _timeline(
    _: CurrentUser, db: DBSession,
    hours: int = Query(24, ge=1, le=168),
):
    now = datetime.now(timezone.utc)
    return [b.model_dump() for b in await timeline(db, now - timedelta(hours=hours), now)]


@router.get("/mitre-cloud")
async def _cloud(_: CurrentUser, db: DBSession, limit: int = Query(50, le=500)):
    return [m.model_dump() for m in await mitre_cloud(db, limit=limit)]


@router.get("/geo")
async def _geo(_: CurrentUser, db: DBSession, hours: int = Query(24, ge=1, le=168)):
    return [g.model_dump() for g in await geo_distribution(db, since=datetime.now(timezone.utc) - timedelta(hours=hours))]   # noqa: E501