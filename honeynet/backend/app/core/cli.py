"""Operator entrypoints exposed via `python -m`."""
from __future__ import annotations

import asyncio
import sys

import typer
import uvicorn

from app.core.bootstrap import bootstrap_async

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def serve(host: str = "0.0.0.0", port: int = 8000, workers: int = 2, reload: bool = False) -> None:
    """Run the FastAPI app via uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=host, port=port, workers=workers if not reload else 1,
        reload=reload, proxy_headers=True, forwarded_allow_ips="*",
        access_log=True,
    )


@cli.command()
def worker(queue: str = "default", concurrency: int = 4, loglevel: str = "INFO") -> None:
    """Run a Celery worker (sync entrypoint for docker images)."""
    from app.workers.celery_app import celery_app
    argv = ["-A", "app.workers.celery_app", "worker",
            "-Q", queue, "--concurrency", str(concurrency),
            "--loglevel", loglevel]
    celery_app.start(argv=argv)


@cli.command()
def bootstrap() -> None:
    """Run the one-shot bootstrap: migrate DB, seed admin user, import dashboards."""
    asyncio.run(bootstrap_async())


if __name__ == "__main__":
    cli()
