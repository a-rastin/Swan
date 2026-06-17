import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "test@example.com"

    r = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_duplicate_register(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "password123",
    })
    r = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "password": "password123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "me@example.com",
        "password": "password123",
    })
    token = login.json()["access_token"]
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"
