"""Zeek notice.log tailer (line-oriented JSON or TSV)."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


def parse_zeek_notice(line: str) -> dict | None:
    """Parse a single Zeek notice.log JSON line into the alert schema."""
    try:
        n = json.loads(line)
    except json.JSONDecodeError:
        return None
    return {
        "source": "zeek",
        "signature": n.get("note", "unknown"),
        "category": n.get("policy", "zeek"),
        "severity": _sev(n.get("level", 3)),
        "src_ip": n.get("src"),
        "dst_ip": n.get("dst"),
        "confidence": 0.0,
        "raw": n,
    }


def _sev(level) -> int:
    try:
        v = int(level)
        return max(1, min(4, 4 - v // 4))  # Zeek severities are inverted
    except (TypeError, ValueError):
        return 3


class ZeekTailer:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.path.join(get_settings().ids_zeek_log_dir, "notice.log"))
        self._task: asyncio.Task | None = None
        self._handlers: list = []

    def on_alert(self, handler) -> None:
        self._handlers.append(handler)

    async def _run(self) -> None:
        if not self.path.exists():
            log.warning("zeek.log_missing", path=str(self.path))
            return
        with self.path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, os.SEEK_END)
            while True:
                line = fh.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                alert = parse_zeek_notice(line)
                if alert is None:
                    continue
                for h in self._handlers:
                    try:
                        await h(alert)
                    except Exception as e:  # noqa: BLE001
                        log.warning("zeek.handler_error", error=str(e))

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="zeek-tailer")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None