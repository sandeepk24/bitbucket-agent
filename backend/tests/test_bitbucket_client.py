"""Bitbucket Data Center client against mocked REST responses."""

from __future__ import annotations

import logging

import httpx
import pytest

from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig, normalize_base_url
from app.providers.bitbucket.errors import (
    BitbucketAuthError,
    BitbucketNotConfiguredError,
    BitbucketNotFoundError,
    BitbucketUnavailableError,
)

TOKEN = "super-secret-token"
BASE = "https://bitbucket.example.com"


def _config(**overrides) -> BitbucketConfig:
    values = {
        "base_url": BASE,
        "token": TOKEN,
        "max_retries": 2,
        "page_limit": 2,
        "connect_timeout": 1.0,
        "timeout": 2.0,
    }
    values.update(overrides)
    return BitbucketConfig(**values)


def _client(handler, **overrides) -> BitbucketClient:
    return BitbucketClient(_config(**overrides), transport=httpx.MockTransport(handler))


def _page(*, values, start=0, is_last=True, next_start=None, limit=2) -> dict:
    payload = {
        "size": len(values),
        "limit": limit,
        "isLastPage": is_last,
        "values": values,
        "start": start,
    }
    if next_start is not None:
        payload["nextPageStart"] = next_start
    return payload


@pytest.mark.asyncio
async def test_unconfigured_client_does_not_call_network():
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json={})

    client = _client(handler, base_url="", token="")
    assert client.is_configured() is False
    with pytest.raises(BitbucketNotConfiguredError):
        await client.list_projects()
    assert calls["count"] == 0
    await client.aclose()


@pytest.mark.asyncio
async def test_health_reports_compatible_10_2_version():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert str(request.url).endswith("/rest/api/latest/application-properties")
        return httpx.Response(
            200,
            json={
                "version": "10.2.8",
                "buildNumber": "1002008000",
                "displayName": "Bitbucket",
            },
        )

    client = _client(handler)
    health = await client.health()
    await client.aclose()
    assert health["reachable"] is True
    assert health["authenticated"] is True
    assert health["version"] == "10.2.8"
    assert health["compatible"] is True
    assert TOKEN not in str(health)


@pytest.mark.asyncio
async def test_health_auth_failure_is_reachable_but_unauthenticated():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"errors": [{"message": "Authentication failed"}]})

    client = _client(handler)
    health = await client.health()
    await client.aclose()
    assert health["reachable"] is True
    assert health["authenticated"] is False
    assert health["compatible"] is False


@pytest.mark.asyncio
async def test_list_projects_follows_next_page_start():
    def handler(request: httpx.Request) -> httpx.Response:
        start = request.url.params.get("start", "0")
        if start == "0":
            return httpx.Response(
                200,
                json=_page(
                    values=[{"key": "DEV", "id": 1, "name": "Development", "public": False}],
                    start=0,
                    is_last=False,
                    next_start=2,
                ),
            )
        return httpx.Response(
            200,
            json=_page(
                values=[{"key": "OPS", "id": 2, "name": "Operations", "public": False}],
                start=2,
                is_last=True,
            ),
        )

    client = _client(handler)
    projects = await client.list_projects()
    await client.aclose()
    assert [item["key"] for item in projects] == ["DEV", "OPS"]


@pytest.mark.asyncio
async def test_list_repos_uses_project_key_and_strips_clone_noise():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/projects/DEV/repos" in str(request.url)
        return httpx.Response(
            200,
            json=_page(
                values=[
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
                                {"name": "ssh", "href": "ssh://git@bitbucket.example.com/dev/payments.git"},
                                {
                                    "name": "http",
                                    "href": "https://bitbucket.example.com/scm/dev/payments.git",
                                },
                            ]
                        },
                    }
                ]
            ),
        )

    client = _client(handler)
    repos = await client.list_repos("DEV")
    await client.aclose()
    assert repos[0]["slug"] == "payments"


@pytest.mark.asyncio
async def test_user_token_uses_basic_auth_when_username_is_set():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["Authorization"]
        return httpx.Response(200, json=_page(values=[]))

    client = _client(handler, username="jsmith")
    await client.list_projects()
    await client.aclose()
    assert seen["authorization"].startswith("Basic ")
    assert TOKEN not in seen["authorization"]


@pytest.mark.asyncio
async def test_retries_transient_503_then_succeeds():
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(503, json={"errors": [{"message": "overloaded"}]})
        return httpx.Response(200, json=_page(values=[{"key": "DEV", "name": "Dev"}]))

    client = _client(handler)
    projects = await client.list_projects()
    await client.aclose()
    assert calls["count"] == 3
    assert projects[0]["key"] == "DEV"


@pytest.mark.asyncio
async def test_401_maps_to_auth_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Authentication failed")

    client = _client(handler)
    with pytest.raises(BitbucketAuthError):
        await client.list_projects()
    await client.aclose()


@pytest.mark.asyncio
async def test_404_maps_to_not_found():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"errors": [{"message": "Project does not exist"}]})

    client = _client(handler)
    with pytest.raises(BitbucketNotFoundError):
        await client.list_repos("MISSING")
    await client.aclose()


@pytest.mark.asyncio
async def test_exhausted_retries_become_unavailable():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    client = _client(handler, max_retries=1)
    with pytest.raises(BitbucketUnavailableError):
        await client.list_projects()
    await client.aclose()


@pytest.mark.asyncio
async def test_logs_never_include_the_token(caplog):
    caplog.set_level(logging.DEBUG)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"version": "10.2.8", "displayName": "Bitbucket"})

    client = _client(handler)
    await client.get_application_properties()
    await client.aclose()
    combined = caplog.text
    assert TOKEN not in combined
    assert "Bearer" not in combined


def test_normalize_base_url_strips_rest_suffix():
    assert (
        normalize_base_url("https://bitbucket.example.com/rest/api/latest")
        == "https://bitbucket.example.com"
    )
