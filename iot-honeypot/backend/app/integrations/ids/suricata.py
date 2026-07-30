"""Suricata EVE JSON client (HTTP+SSE or HTTP polling)."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


def parse_suricata_event(eve: dict) -> dict:
    """Map a single Suricata EVE event to the normalised alert schema."""
    return {
        "source": "suricata",
        "signature": eve.get("alert", {}).get("signature", eve.get("event_type", "unknown")),
        "category": eve.get("alert", {}).get("category", eve.get("event_type", "unknown")),
        "severity": _sev(eve.get("alert", {}).get("severity", 3)),
        "src_ip": eve.get("src_ip"),
        "dst_ip": eve.get("dest_ip"),
        "confidence": float(eve.get("alert", {}).get("confidence", 0) or 0),
        "raw": eve,
    }


def _sev(s: int | str | None) -> int:
    try:
        v = int(s)
        return max(1, min(4, v))
    except (TypeError, ValueError):
        return 3


class SuricataClient:
    def __init__(self, timeout: float = 5.0) -> None:
        self.url = get_settings().ids_suricata_eve_url
        self._client = httpx.AsyncClient(timeout=timeout)

    async def fetch_recent(self) -> list[dict]:
        try:
            r = await self._client.get(self.url, params={"limit": 50})
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return [parse_suricata_event(e) for e in data]
        except httpx.HTTPError:
            pass
        return []

    async def aclose(self) -> None:
        await self._client.aclose()