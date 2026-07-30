"""Honeypot CRUD + event ingest tests."""
import pytest

pytestmark = pytest.mark.asyncio


async def _admin_token(client) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "username": "admin",
            "password": "Str0ngP4ssword!",
        },
    )
    r = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "Str0ngP4ssword!"}
    )
    return r.json()["access_token"]


async def test_honeypot_crud_and_event_ingest(client):
    token = await _admin_token(client)
    H = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/honeypots",
        headers=H,
        json={"name": "cam1", "kind": "camera-rtsp", "host": "0.0.0.0", "port": 554},
    )
    assert r.status_code == 201, r.text
    hp = r.json()
    hp_id = hp["id"]

    r = await client.post(
        f"/api/v1/events/{hp_id}/events",
        json={
            "event_type": "probe",
            "protocol": "rtsp",
            "payload": {"uri": "/onvif/device_service"},
            "src_ip": "203.0.113.7",
            "src_port": 50001,
            "dst_port": 554,
        },
    )
    assert r.status_code == 201, r.text

    r = await client.get(f"/api/v1/events/{hp_id}/events", headers=H)
    assert r.status_code == 200
    assert len(r.json()) >= 1