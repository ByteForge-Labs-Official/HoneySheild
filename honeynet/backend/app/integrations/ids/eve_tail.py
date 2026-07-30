"""Suricata eve.json tail — pushes IDS events into Elasticsearch."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()
EVE_PATH = Path("/var/log/suricata/eve.json")
ES_URL   = "http://elasticsearch:9200/honeypot-suricata/_doc"


async def run(stop: asyncio.Event | None = None) -> None:
    """Tail eve.json; each line is one JSON record that we re-emit to ES."""
    if not EVE_PATH.exists():
        logger.warning("ids.eve.missing", path=str(EVE_PATH))
        await asyncio.sleep(5)

    async with httpx.AsyncClient(timeout=5) as http:
        with EVE_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, 2)            # tail only new content
            while not (stop and stop.is_set()):
                line = fh.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                try:
                    rec: dict[str, Any] = __import__("orjson").loads(line)
                except Exception:    # noqa: BLE001
                    continue
                try:
                    await http.post(ES_URL, json=rec)
                except Exception as e:    # noqa: BLE001
                    logger.error("ids.eve.forward_failed", error=str(e))