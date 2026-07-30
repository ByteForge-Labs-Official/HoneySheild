"""Health + version endpoint tests."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_health_returns_ok(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_version(client):
    r = await client.get("/api/v1/version")
    assert r.status_code == 200
    body = r.json()
    assert "name" in body and "version" in body