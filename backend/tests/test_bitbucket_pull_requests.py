"""Pull request client and API coverage using Bitbucket-shaped fixtures."""

from __future__ import annotations

import httpx
import pytest

from app.api.deps import get_bitbucket_client
from app.main import app
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig
from app.providers.bitbucket.errors import BitbucketNotFoundError
from tests.fixtures.bitbucket_prs import (
    DECLINED_PR,
    MERGED_PR,
    OPEN_PR,
    PR_CHANGES,
    PR_COMMITS,
    page,
)

TOKEN = "super-secret-token"
PR_ROOT = "/rest/api/latest/projects/DEV/repos/payments/pull-requests"


def _config() -> BitbucketConfig:
    return BitbucketConfig(base_url="https://bitbucket.example.com", token=TOKEN)


def _client(handler) -> BitbucketClient:
    return BitbucketClient(_config(), transport=httpx.MockTransport(handler))


def _router(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url.endswith("/pull-requests/42/commits") or "/pull-requests/42/commits?" in url:
        return httpx.Response(200, json=page(PR_COMMITS))
    if url.endswith("/pull-requests/42/changes") or "/pull-requests/42/changes?" in url:
        return httpx.Response(200, json=page(PR_CHANGES))
    if "/pull-requests/42" in url and "/commits" not in url and "/changes" not in url:
        return httpx.Response(200, json=OPEN_PR)
    if "/pull-requests" in url:
        state = request.url.params.get("state", "OPEN")
        values = {"OPEN": [OPEN_PR], "MERGED": [MERGED_PR], "DECLINED": [DECLINED_PR]}.get(
            state, [OPEN_PR, MERGED_PR, DECLINED_PR]
        )
        return httpx.Response(200, json=page(values))
    return httpx.Response(404, json={"errors": [{"message": "not found"}]})


@pytest.mark.asyncio
async def test_list_pull_requests_filters_by_state_and_pages():
    seen_states: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        start = request.url.params.get("start", "0")
        seen_states.append(request.url.params.get("state", ""))
        if start == "0":
            return httpx.Response(
                200,
                json=page([OPEN_PR], start=0, is_last=False, next_start=1, limit=1),
            )
        return httpx.Response(200, json=page([MERGED_PR], start=1, is_last=True, limit=1))

    client = _client(handler)
    items = await client.list_pull_requests("DEV", "payments", state="ALL")
    await client.aclose()
    assert [item["id"] for item in items] == [42, 7]
    assert "ALL" in seen_states


@pytest.mark.asyncio
async def test_get_pull_request_includes_reviewers_and_branches():
    client = _client(_router)
    pr = await client.get_pull_request("DEV", "payments", 42)
    await client.aclose()
    assert pr["id"] == 42
    assert pr["fromRef"]["displayId"] == "feature/token-redaction"
    assert pr["toRef"]["displayId"] == "main"
    assert pr["reviewers"][0]["status"] == "APPROVED"
    assert pr["reviewers"][1]["status"] == "NEEDS_WORK"


@pytest.mark.asyncio
async def test_pr_commits_and_changes():
    client = _client(_router)
    commits = await client.list_pull_request_commits("DEV", "payments", 42)
    changes = await client.list_pull_request_changes("DEV", "payments", 42)
    await client.aclose()
    assert commits[0]["displayId"] == "a1b2c3d"
    assert changes[0]["path"]["toString"].endswith("client.py")
    assert changes[1]["type"] == "ADD"


@pytest.mark.asyncio
async def test_missing_pull_request_is_not_found():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"errors": [{"message": "Pull request not found"}]})

    client = _client(handler)
    with pytest.raises(BitbucketNotFoundError):
        await client.get_pull_request("DEV", "payments", 404)
    await client.aclose()


@pytest.fixture
def override_bitbucket():
    client = _client(_router)
    app.dependency_overrides[get_bitbucket_client] = lambda: client
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_prs_api(client, override_bitbucket):
    resp = await client.get(
        "/api/bitbucket/projects/DEV/repos/payments/pull-requests",
        params={"state": "OPEN"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    item = data["items"][0]
    assert item["id"] == 42
    assert item["source_branch"] == "feature/token-redaction"
    assert item["destination_branch"] == "main"
    assert item["author"]["display_name"] == "Tom Rivera"
    assert item["reviewer_count"] == 2
    assert item["approved_count"] == 1
    assert TOKEN not in str(data)


@pytest.mark.asyncio
async def test_pr_detail_api_bundles_commits_and_files(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects/DEV/repos/payments/pull-requests/42")
    assert resp.status_code == 200
    data = resp.json()
    pr = data["pull_request"]
    assert pr["reviewers"][0]["status"] == "APPROVED"
    assert pr["html_url"].endswith("/pull-requests/42")
    assert data["commits"][0]["message"].startswith("Redact")
    assert data["changes"][0]["path"].endswith("client.py")
    assert data["changes"][1]["change_type"] == "ADD"
    assert TOKEN not in str(data)


@pytest.mark.asyncio
async def test_pr_list_unconfigured(client):
    resp = await client.get("/api/bitbucket/projects/DEV/repos/payments/pull-requests")
    assert resp.status_code == 503
