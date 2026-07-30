"""Attacks + analytics adapter routes for the React SOC dashboard."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import require_roles
from app.db.session import DbSession
from app.services.honeypot_service import HoneypotService

router = APIRouter()

SEVERITY_MAP = {
    "exploit": "critical",
    "brute_force": "high",
    "scan": "medium",
    "login": "medium",
    "command": "high",
}

COUNTRY_GEO: dict[str, dict[str, float]] = {
    "RU": {"lat": 61.5, "lon": 105.3},
    "CN": {"lat": 35.9, "lon": 104.2},
    "DE": {"lat": 51.2, "lon": 10.5},
    "TH": {"lat": 15.9, "lon": 100.9},
    "US": {"lat": 37.1, "lon": -95.7},
    "UA": {"lat": 48.4, "lon": 31.2},
    "NL": {"lat": 52.1, "lon": 5.3},
    "BR": {"lat": -14.2, "lon": -51.9},
}


def _event_to_attack(ev: dict) -> dict:
    payload = ev.get("payload") or {}
    country = payload.get("country")
    geo = COUNTRY_GEO.get(country or "", {})
    severity = SEVERITY_MAP.get(ev.get("event_type", ""), "low")

    # Timestamps
    created = ev.get("created_at")
    if isinstance(created, datetime):
        ts = created.isoformat()
    else:
        ts = str(created) if created else datetime.now(tz=timezone.utc).isoformat()

    return {
        "id": ev.get("id", ""),
        "timestamp": ts,
        "source_ip": str(ev.get("src_ip") or ""),
        "source_port": ev.get("src_port"),
        "destination_port": ev.get("dst_port"),
        "protocol": ev.get("protocol", "ssh"),
        "honeypot_id": str(ev.get("honeypot_id", "")),
        "country": country,
        "latitude": geo.get("lat"),
        "longitude": geo.get("lon"),
        "severity": severity,
        "payload_summary": f"user={payload.get('username','?')} pass={payload.get('password','?')}",
        "username": payload.get("username"),
        "password": payload.get("password"),
        "raw_event": payload,
    }


@router.get("/attacks", summary="Paginated attack list for dashboard")
async def list_attacks(
    session: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> dict[str, Any]:
    limit = min(page_size * page, 500)
    rows = await HoneypotService(session).recent_events(None, limit=limit)
    attacks = [_event_to_attack(r) for r in rows]
    start = (page - 1) * page_size
    page_items = attacks[start: start + page_size]
    return {
        "items": page_items,
        "total": len(attacks),
        "page": page,
        "page_size": page_size,
    }


@router.get("/analytics/stats", summary="Aggregate attack stats for dashboard")
async def analytics_stats(
    session: DbSession,
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> dict[str, Any]:
    rows = await HoneypotService(session).recent_events(None, limit=500)
    attacks = [_event_to_attack(r) for r in rows]

    by_severity: dict[str, int] = defaultdict(int)
    by_protocol: dict[str, int] = defaultdict(int)
    country_counts: dict[str, int] = defaultdict(int)
    top_ips: dict[str, int] = defaultdict(int)

    for a in attacks:
        by_severity[a["severity"]] += 1
        by_protocol[a["protocol"]] += 1
        if a["country"]:
            country_counts[a["country"]] += 1
        if a["source_ip"]:
            top_ips[a["source_ip"]] += 1

    by_country = [
        {
            "country": c,
            "count": n,
            "lat": COUNTRY_GEO.get(c, {}).get("lat"),
            "lon": COUNTRY_GEO.get(c, {}).get("lon"),
        }
        for c, n in sorted(country_counts.items(), key=lambda x: -x[1])
    ]

    top_ips_list = [
        {"ip": ip, "count": n}
        for ip, n in sorted(top_ips.items(), key=lambda x: -x[1])[:10]
    ]

    # 24-hour timeline (hourly buckets)
    now = datetime.now(tz=timezone.utc)
    buckets: dict[str, int] = {}
    for i in range(24):
        bk = (now - timedelta(hours=23 - i)).strftime("%Y-%m-%dT%H:00:00Z")
        buckets[bk] = 0

    for a in attacks:
        try:
            dt = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
            bk = dt.strftime("%Y-%m-%dT%H:00:00Z")
            if bk in buckets:
                buckets[bk] += 1
        except (ValueError, AttributeError):
            pass

    timeline = [{"bucket": bk, "count": n} for bk, n in sorted(buckets.items())]

    return {
        "total": len(attacks),
        "by_severity": dict(by_severity),
        "by_protocol": dict(by_protocol),
        "by_country": by_country,
        "timeline": timeline,
        "top_ips": top_ips_list,
    }


@router.get("/analytics/timeline", summary="Attack timeline")
async def analytics_timeline(
    session: DbSession,
    range: str = Query(default="24h"),
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> list[dict[str, Any]]:
    hours = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}.get(range, 24)
    rows = await HoneypotService(session).recent_events(None, limit=500)
    attacks = [_event_to_attack(r) for r in rows]

    now = datetime.now(tz=timezone.utc)
    buckets: dict[str, int] = {}
    for i in range(hours):
        bk = (now - timedelta(hours=hours - 1 - i)).strftime("%Y-%m-%dT%H:00:00Z")
        buckets[bk] = 0

    for a in attacks:
        try:
            dt = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
            bk = dt.strftime("%Y-%m-%dT%H:00:00Z")
            if bk in buckets:
                buckets[bk] += 1
        except (ValueError, AttributeError):
            pass

    return [{"bucket": bk, "count": n} for bk, n in sorted(buckets.items())]


@router.get("/analytics/top-ips", summary="Top attacker IPs")
async def analytics_top_ips(
    session: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> list[dict[str, Any]]:
    rows = await HoneypotService(session).recent_events(None, limit=500)
    ip_counts: dict[str, dict] = defaultdict(lambda: {"count": 0, "country": None})
    for r in rows:
        ip = str(r.get("src_ip") or "")
        if ip:
            ip_counts[ip]["count"] += 1
            ip_counts[ip]["country"] = (r.get("payload") or {}).get("country")

    return [
        {"ip": ip, "count": d["count"], "country": d["country"]}
        for ip, d in sorted(ip_counts.items(), key=lambda x: -x[1]["count"])[:limit]
    ]


@router.get("/analytics/geo", summary="Geo distribution")
async def analytics_geo(
    session: DbSession,
    user_roles: dict = Depends(require_roles("analyst", "admin")),
) -> list[dict[str, Any]]:
    rows = await HoneypotService(session).recent_events(None, limit=500)
    country_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        c = (r.get("payload") or {}).get("country")
        if c:
            country_counts[c] += 1
    return [
        {
            "country": c,
            "count": n,
            "lat": COUNTRY_GEO.get(c, {}).get("lat"),
            "lon": COUNTRY_GEO.get(c, {}).get("lon"),
        }
        for c, n in sorted(country_counts.items(), key=lambda x: -x[1])
    ]
