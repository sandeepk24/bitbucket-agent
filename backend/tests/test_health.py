"""Health, readiness, and settings endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["bitbucket_configured"] is False
    assert data["bamboo_configured"] is False
    assert data["bedrock_configured"] is False
    assert data["strands_configured"] is False
    assert data["ai_provider"] in {"bedrock", "strands"}
    payload = str(data).lower()
    assert "bitbucket_token" not in payload
    assert "bamboo_token" not in payload
    assert "token" not in payload


@pytest.mark.asyncio
async def test_ready_endpoint(client):
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_settings_omits_secrets(client):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "bitbucket_token" not in data
    assert "bamboo_token" not in data
    assert "bitbucket_base_url" in data
    assert data["bedrock_enabled"] is False
    assert data["strands_enabled"] is False


@pytest.mark.asyncio
async def test_root_metadata(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bitbucket Agent"
    assert data["health"] == "/api/v1/health"
