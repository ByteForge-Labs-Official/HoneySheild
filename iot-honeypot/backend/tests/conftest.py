"""Pytest fixtures: in-memory SQLite + a test client."""
from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.db.session as session_module
from app.db.session import Base, get_session
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def client(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _override():
        async with Session() as s:
            yield s

    app = create_app()
    app.dependency_overrides[get_session] = _override
    # Avoid actually pinging Redis during tests
    async def _noop():
        class _R:
            async def ping(self_inner): return True
            async def aclose(self_inner): return None
        return _R()
    app.dependency_overrides[__import__("app.integrations.redis.client", fromlist=["get_redis"]).get_redis] = _noop  # noqa: E501

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac