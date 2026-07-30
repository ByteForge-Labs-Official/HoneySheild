"""Rotating file handler + retention cleanup helper."""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler as _StdRotatingFileHandler
from pathlib import Path

from app.core.logging.formatter import HoneynetJsonFormatter


class RotatingFileHandler(_StdRotatingFileHandler):
    """Adds the JSON formatter and ensures the parent directory exists."""

    def __init__(
        self,
        filename: str | os.PathLike,
        *,
        max_bytes: int = 50 * 1024 * 1024,
        backup_count: int = 10,
        level: int = logging.INFO,
        encoding: str = "utf-8",
    ) -> None:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename=str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=False,
        )
        self.setLevel(level)
        self.setFormatter(HoneynetJsonFormatter())


def build_retention_cleanup(directory: str | os.PathLike, retention_days: int):
    """Return a Celery beat-callable that deletes old rotated logs.

    ```python
    from app.core.logging.handlers.file import build_retention_cleanup
    purge_logs = build_retention_cleanup(settings.log_dir, settings.log_retention_days)

    @app.on_after_configure.connect
    def setup_periodic_tasks(sender, **kwargs):
        sender.add_periodic_task(timedelta(hours=6), purge_logs.s())
    ```
    """
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    from app.workers.celery_app import celery_app  # local import — optional dep

    @celery_app.task(name="app.workers.tasks.maintenance_tasks.purge_old_logs")
    def purge_old_logs() -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        removed: list[str] = []
        for path in Path(directory).glob("*"):
            if not path.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if mtime < cutoff:
                try:
                    path.unlink()
                    removed.append(str(path))
                except OSError:
                    continue
        return {"removed": removed, "directory": str(directory), "retention_days": retention_days}

    return purge_old_logs