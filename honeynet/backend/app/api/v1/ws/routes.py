"""WebSocket bridge — relays live attack events to the React dashboard."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import orjson
import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.config.constants import LIVE_ATTACKS_PUBSUB
from app.core.security.jwt import decode_token
from app.integrations.redis.client import get_redis

logger = structlog.get_logger()
router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("/live")
async def live(
    ws: WebSocket,
    token: str = Query(...),                           # noqa: B008
):
    try:
        decode_token(token, expected_type="access")
    except Exception:                                  # noqa: BLE001
        await ws.close(code=status.WS_1008_POLICY_VIOLATION); return

    await ws.accept()
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(LIVE_ATTACKS_PUBSUB)
    try:
        async for message in _reader(pubsub):
            await ws.send_bytes(orjson.dumps({"type": "attack", "data": message}))
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(LIVE_ATTACKS_PUBSUB)
        await pubsub.close()


async def _reader(pubsub) -> AsyncIterator[dict]:
    """Bridge blocking pubsub iterator into an async generator."""
    loop = asyncio.get_running_loop()
    while True:
        msg = await loop.run_in_executor(None, lambda: pubsub.parse_response(block=True, timeout=1.0))
        if not msg:
            await asyncio.sleep(0.05); continue
        if msg.get("type") != "message":
            continue
        data = msg.get("data")
        if isinstance(data, bytes):
            try:    yield orjson.loads(data)
            except: pass