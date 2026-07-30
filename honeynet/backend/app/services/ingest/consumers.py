"""Stream consumer that pulls from Redis stream and persists to Postgres."""
from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.constants import RAW_ATTACKS_STREAM
from app.db.session import async_session
from app.integrations.redis.client import get_redis
from app.models.attack import Attack, Event
from app.models.session import Session as SessionModel
from app.services.ingest.normalizer import normalize_event, normalize_line
from app.services.geoip import enrich_ip

logger = structlog.get_logger()
CONSUMER_GROUP = "honeynet"
CONSUMER_NAME  = "worker-1"


async def run_consumer(stop: asyncio.Event | None = None) -> None:
    r = await get_redis()
    try:
        await r.xgroup_create(RAW_ATTACKS_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:  # noqa: BLE001
        pass  # BUSYGROUP is expected after first start

    while not (stop and stop.is_set()):
        try:
            res = await r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                streams={RAW_ATTACKS_STREAM: ">"},
                count=128,
                block=2000,
            )
        except Exception as e:        # noqa: BLE001
            logger.error("ingest.read_failed", error=str(e))
            await asyncio.sleep(1)
            continue

        for _stream, entries in res or []:
            for entry_id, fields in entries:
                try:
                    payload = _decode(fields)
                    await _persist(payload)
                    await r.xack(RAW_ATTACKS_STREAM, CONSUMER_GROUP, entry_id)
                except Exception as e:   # noqa: BLE001
                    logger.error("ingest.persist_failed", entry=entry_id, error=str(e))


def _decode(fields: dict[bytes | str, bytes | str]) -> dict[str, Any]:
    raw = fields.get(b"payload") or fields.get("payload")
    if isinstance(raw, bytes):
        raw = raw.decode()
    import orjson
    return orjson.loads(raw)


async def _persist(payload: dict[str, Any]) -> None:
    ev = await normalize_event(payload)
    async with async_session() as db:                  # type: AsyncSession
        await _upsert(db, ev, payload)


async def _upsert(db: AsyncSession, ev: dict[str, Any], payload: dict[str, Any]) -> None:
    """Upsert session + attack + event idempotently."""
    geo = await enrich_ip(ev["src_ip"]) if ev["src_ip"] else {}

    # --- session --------------------------------------------------------
    stmt = pg_insert(SessionModel).values(
        id=payload["session_id"],
        device_id=payload["device_id"],
        remote_ip=ev["src_ip"] or "0.0.0.0",
        started_at=ev["ts"],
        transport=ev["protocol"],
        country_iso=geo.get("country_iso"),
        asn=geo.get("asn"),
        user_agent=normalize_line(payload.get("user_agent")),
    ).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(stmt)

    # --- attack ---------------------------------------------------------
    stmt = pg_insert(Attack).values(
        id=payload["attack_id"],
        session_id=payload["session_id"],
        protocol=ev["protocol"],
        started_at=ev["ts"],
        severity=ev["severity"],
        src_ip=ev["src_ip"] or "0.0.0.0",
        dst_port=ev["dst_port"],
    ).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(stmt)

    # --- event ----------------------------------------------------------
    db.add(Event(
        attack_id=payload["attack_id"],
        ts=ev["ts"],
        kind=ev["kind"],
        severity=ev["severity"],
        payload=ev["meta"],
        src_ip=ev["src_ip"],
        dst_ip=ev["dst_ip"],
        raw=ev["raw"],
    ))
    await db.commit()