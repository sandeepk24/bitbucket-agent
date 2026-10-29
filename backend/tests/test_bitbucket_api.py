"""HTTP API wrappers around the Bitbucket client."""

from __future__ import annotations

import httpx
import pytest

from app.api.deps import get_bitbucket_client
from app.main import app
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig

TOKEN = "super-secret-token"


def _page(values, *, is_last=True, start=0, next_start=None):
    payload = {
        "size": len(values),
        "limit": 25,
        "isLastPage": is_last,
        "values": values,
        "start": start,
    }
    if next_start is not None:
        payload["nextPageStart"] = next_start
    return payload


@pytest.fixture
def override_bitbucket(request):
    handler = request.param
    client = BitbucketClient(
        BitbucketConfig(base_url="https://bitbucket.example.com", token=TOKEN),
        transport=httpx.MockTransport(handler),
    )
    app.dependency_overrides[get_bitbucket_client] = lambda: client
    yield
    app.dependency_overrides.clear()


def _props(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"version": "10.2.8", "buildNumber": "1002008000", "displayName": "Bitbucket"},
    )


def _projects(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json=_page([{"key": "DEV", "id": 1, "name": "Development", "public": False, "type": "NORMAL"}]),
    )


def _repos(request: httpx.Request) -> httpx.Response:
    assert "/projects/DEV/repos" in str(request.url)
    return httpx.Response(
        200,
        json=_page(
            [
                {
                    "slug": "payments",
                    "id": 11,
                    "name": "payments",
                    "scmId": "git",
                    "state": "AVAILABLE",
                    "public": False,
                    "project": {"key": "DEV"},
                    "links": {
                        "clone": [
                            {"name": "http", "href": "https://bitbucket.example.com/scm/dev/payments.git"}
                        ]
                    },
                }
            ]
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("override_bitbucket", [_props], indirect=True)
async def test_bitbucket_health_endpoint(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "10.2.8"
    assert data["compatible"] is True
    assert data["authenticated"] is True
    assert TOKEN not in str(data).lower()
    assert "token" not in str(data).lower()


@pytest.mark.asyncio
async def test_bitbucket_health_unconfigured(client):
    resp = await client.get("/api/bitbucket/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["reachable"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("override_bitbucket", [_projects], indirect=True)
async def test_list_projects_endpoint(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["items"][0]["key"] == "DEV"
    assert TOKEN not in str(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("override_bitbucket", [_repos], indirect=True)
async def test_list_repos_endpoint(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects/DEV/repos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_key"] == "DEV"
    assert data["items"][0]["slug"] == "payments"
    assert data["items"][0]["clone_http"].endswith("/payments.git")


@pytest.mark.asyncio
async def test_projects_unconfigured_returns_503(client):
    resp = await client.get("/api/bitbucket/projects")
    assert resp.status_code == 503
    assert "token" not in resp.text.lower()


def _unauthorized(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(401, json={"errors": [{"message": "Authentication failed"}]})


@pytest.mark.asyncio
@pytest.mark.parametrize("override_bitbucket", [_unauthorized], indirect=True)
async def test_auth_failure_does_not_leak_token(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects")
    assert resp.status_code == 502
    assert TOKEN not in resp.text
    assert resp.json()["detail"] == "Bitbucket authentication failed"


def _missing(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(404, json={"errors": [{"message": "Project does not exist."}]})


@pytest.mark.asyncio
@pytest.mark.parametrize("override_bitbucket", [_missing], indirect=True)
async def test_missing_project_returns_404(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects/NOPE/repos")
    assert resp.status_code == 404
