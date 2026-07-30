"""Analytics aggregations — served from Postgres materialized views."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analytics import GeoPoint, MitreTag, TimelineBucket, TopIp


async def top_ips(db: AsyncSession, limit: int = 50) -> list[TopIp]:
    rows = await db.execute(text("""
        SELECT src_ip, count(*) AS hits, max(started_at) AS last_seen
        FROM attacks
        WHERE started_at > now() - interval '24 hours'
        GROUP BY src_ip ORDER BY hits DESC LIMIT :lim
    """), {"lim": limit})
    return [TopIp(src_ip=r[0], hits=r[1], last_seen=r[2]) for r in rows.all()]


async def timeline(db: AsyncSession, since: datetime, until: datetime) -> list[TimelineBucket]:
    rows = await db.execute(text("""
        SELECT date_trunc('minute', started_at) AS bucket,
               protocol, count(*) AS attacks,
               count(DISTINCT src_ip) AS distinct_ips
        FROM attacks
        WHERE started_at BETWEEN :since AND :until
        GROUP BY 1, 2 ORDER BY 1
    """), {"since": since, "until": until})
    return [TimelineBucket(bucket=r[0], protocol=r[1], attacks=r[2], distinct_ips=r[3]) for r in rows.all()]


async def mitre_cloud(db: AsyncSession, limit: int = 50) -> list[MitreTag]:
    rows = await db.execute(text("""
        SELECT tag, count, last_seen
        FROM (
            SELECT unnest(mitre_tags) AS tag,
                   count(*) AS count,
                   max(started_at) AS last_seen
            FROM attacks
            GROUP BY 1
        ) t
        ORDER BY count DESC LIMIT :lim
    """), {"lim": limit})
    return [MitreTag(tag=r[0], count=r[1], last_seen=r[2]) for r in rows.all()]


async def geo_distribution(db: AsyncSession, since: datetime | None = None) -> list[GeoPoint]:
    since = since or (datetime.now(timezone.utc) - timedelta(hours=24))
    rows = await db.execute(text("""
        SELECT s.country_iso, count(*) AS hits
        FROM attacks a JOIN sessions s ON s.id = a.session_id
        WHERE a.started_at > :since AND s.country_iso IS NOT NULL
        GROUP BY s.country_iso
    """), {"since": since})
    from app.services.geoip import country_meta
    out: list[GeoPoint] = []
    for r in rows.all():
        iso, hits = r[0], r[1]
        meta = await country_meta(iso)
        if not meta:
            continue
        out.append(GeoPoint(country_iso=iso, country_name=meta["name"], lat=meta["lat"], lon=meta["lon"], hits=hits))
    return out