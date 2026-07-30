"""Two streaming sources: SQLite (poll) and log file (inotify)."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import aiosqlite
import asyncpg
import orjson
import redis.asyncio as aioredis
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import Settings
from app.metrics import EVENTS_SHIPPED_TOTAL, INGEST_LAG_SECONDS, SHIP_ERRORS_TOTAL

# The honeypot's schema — mirrored here so we don't have to introspect.
_KNOWN_TABLES = ("auth_attempts", "commands", "sessions")


# ---------------------------------------------------------------------------
# SQLite poller — reads rows appended since the last checkpoint.
# ---------------------------------------------------------------------------

class DbTail:
    def __init__(self, cfg: Settings) -> None:
        self.cfg   = cfg
        self._seen_id: dict[str, int] = {t: 0 for t in _KNOWN_TABLES}

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                if not self.cfg.honeypot_db.exists():
                    await asyncio.wait_for(stop.wait(), timeout=self.cfg.poll_interval_s)
                    continue

                async with aiosqlite.connect(self.cfg.honeypot_db) as db:
                    for table in _KNOWN_TABLES:
                        last = self._seen_id[table]
                        async with db.execute(
                            f"SELECT * FROM {table} WHERE id > ? ORDER BY id ASC LIMIT 500",
                            (last,),
                        ) as cur:
                            rows = await cur.fetchall()
                            cols = [c[0] for c in cur.description] if cur.description else []
                            if rows:
                                EVENTS_SHIPPED_TOTAL.labels(source="db").inc(len(rows))
                                self._seen_id[table] = rows[-1][0]
                                # Cheap & dirty: publish to a Redis stream so the
                                # dashboard's WebSocket fans out instantly.
                                await _publish_redis(self.cfg, table, cols, rows)
                                INGEST_LAG_SECONDS.set(0.0)
            except Exception as exc:
                SHIP_ERRORS_TOTAL.labels(target="db", kind=type(exc).__name__).inc()

            try:
                await asyncio.wait_for(stop.wait(), timeout=self.cfg.poll_interval_s)
            except asyncio.TimeoutError:
                continue

        INGEST_LAG_SECONDS.set(time.time())


# ---------------------------------------------------------------------------
# Log tail — inotify watches the file, each new line is shipped as JSON.
# ---------------------------------------------------------------------------

class _LogHandler(FileSystemEventHandler):
    def __init__(self, cfg: Settings, loop: asyncio.AbstractEventLoop) -> None:
        self.cfg  = cfg
        self.loop = loop

    def on_modified(self, event) -> None:       # type: ignore[override]
        if event.is_directory or Path(event.src_path) != self.cfg.honeypot_log:
            return
        # Read whatever hasn't been read yet.
        asyncio.run_coroutine_threadsafe(self._drain(), self.loop)

    async def _drain(self) -> None:
        try:
            with self.cfg.honeypot_log.open("rb") as fh:
                fh.seek(self._offset)
                buf = fh.read()
                self._offset = fh.tell()
            for line in buf.splitlines():
                if not line:
                    continue
                try:
                    payload: dict[str, Any] = orjson.loads(line)
                except orjson.JSONDecodeError:
                    payload = {"raw": line.decode("utf-8", "replace")}
                EVENTS_SHIPPED_TOTAL.labels(source="log").inc()
                await _publish_redis(self.cfg, "log_line", ("payload",), [(orjson.dumps(payload),)])
        except FileNotFoundError:
            pass
        except Exception as exc:
            SHIP_ERRORS_TOTAL.labels(target="log", kind=type(exc).__name__).inc()

    _offset: int = 0


class LogTail:
    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg

    async def run(self, stop: asyncio.Event) -> None:
        loop = asyncio.get_running_loop()
        handler = _LogHandler(self.cfg, loop)
        handler._offset = self.cfg.honeypot_log.stat().st_size if self.cfg.honeypot_log.exists() else 0
        observer = Observer()
        observer.schedule(handler, str(self.cfg.honeypot_log.parent), recursive=False)
        observer.daemon = True
        observer.start()
        try:
            await stop.wait()
        finally:
            observer.stop()
            observer.join(timeout=2)


# ---------------------------------------------------------------------------
# Shared helper — fan-out to Redis Streams (the dashboard consumes these).
# ---------------------------------------------------------------------------

async def _publish_redis(
    cfg: Settings,
    stream: str,
    columns: tuple[str, ...],
    rows: list[tuple[Any, ...]],
) -> None:
    try:
        client = aioredis.from_url(cfg.redis_url, decode_responses=True)
        async with client:
            pipe = client.pipeline(transaction=False)
            for row in rows:
                payload = dict(zip(columns, row))
                pipe.xadd(f"honeynet:events:{stream}", {"data": orjson.dumps(payload).decode()})
            await pipe.execute()
    except Exception as exc:
        SHIP_ERRORS_TOTAL.labels(target="redis", kind=type(exc).__name__).inc()