"""Grafana dashboard provisioning client."""
from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config.settings import get_settings


async def import_dashboards(folder: str) -> None:
    """POST every *.json file under `folder` to Grafana's /api/dashboards/import."""
    s = get_settings()
    base = f"http://grafana:3000/api/dashboards/import"
    auth = (s.grafana_admin_user, s.grafana_admin_password)
    for path in Path(folder).rglob("*.json"):
        payload = {"dashboard": path.read_text(), "overwrite": True, "inputs": []}
        async with httpx.AsyncClient(auth=auth, timeout=10) as c:
            r = await c.post(base, json=payload)
            r.raise_for_status()