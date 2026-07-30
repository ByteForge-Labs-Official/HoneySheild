"""Auth flow tests (register, login, refresh, me)."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_register_login_refresh_me(client):
    payload = {
        "email": "analyst@example.com",
        "username": "analyst",
        "password": "Str0ngP4ssword!",
        "full_name": "Test Analyst",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    r = await client.post(
        "/api/v1/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["username"] == "analyst"

    r = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 200