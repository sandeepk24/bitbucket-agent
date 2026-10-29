"""Before/after comparison against mocked Bitbucket 10.2 REST."""

from __future__ import annotations

from urllib.parse import unquote, urlparse

import httpx
import pytest

from app.api.deps import get_bitbucket_client
from app.main import app
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig
from app.providers.bitbucket.errors import BitbucketError
from app.schemas.comparison import parse_diff_stats
from tests.fixtures.bitbucket_comparison import (
    AFTER_CLIENT,
    AFTER_RENAME,
    AFTER_SECRETS,
    BEFORE_CLIENT,
    BEFORE_DELETED,
    BEFORE_RENAME,
    BINARY_PATH,
    CLIENT_PATH,
    COMPARISON_CHANGES,
    COMPARISON_COMMITS,
    DELETED_PATH,
    HEAD_SHA,
    MERGE_BASE,
    MERGE_BASE_SHA,
    PR_DIFF,
    RAW_FILES,
    RENAME_DEST,
    RENAME_SRC,
    SECRETS_PATH,
    TARGET_SHA,
    TRUNCATED_DIFF,
)
from tests.fixtures.bitbucket_prs import OPEN_PR, page

TOKEN = "super-secret-token"
PR_ROOT = "/rest/api/latest/projects/DEV/repos/payments/pull-requests/42"


def _config(**overrides) -> BitbucketConfig:
    values = {
        "base_url": "https://bitbucket.example.com",
        "token": TOKEN,
        "max_file_bytes": 1_024,
    }
    values.update(overrides)
    return BitbucketConfig(**values)


def _client(handler, **overrides) -> BitbucketClient:
    return BitbucketClient(_config(**overrides), transport=httpx.MockTransport(handler))


def _raw_key(url: str) -> tuple[str, str] | None:
    parsed = urlparse(str(url))
    marker = "/raw/"
    if marker not in parsed.path:
        return None
    path = unquote(parsed.path.split(marker, 1)[1])
    at = httpx.QueryParams(parsed.query).get("at", "")
    return path, at


def _comparison_handler(
    request: httpx.Request,
    *,
    merge_base: dict | None = MERGE_BASE,
    diff: dict = PR_DIFF,
    raw: dict[tuple[str, str], str] | bytes | dict = RAW_FILES,
    binary_paths: frozenset[str] = frozenset({BINARY_PATH}),
) -> httpx.Response:
    url = str(request.url)
    if url.endswith("/merge-base"):
        if merge_base is None:
            return httpx.Response(404, json={"errors": [{"message": "no merge-base"}]})
        return httpx.Response(200, json=merge_base)
    if "/diff" in url:
        expected_since = merge_base["id"] if merge_base else MERGE_BASE_SHA
        assert request.url.params.get("sinceId") == expected_since
        assert request.url.params.get("untilId") == HEAD_SHA
        assert "/" not in (request.url.params.get("sinceId") or "")
        return httpx.Response(200, json=diff)
    key = _raw_key(url)
    if key:
        assert httpx.QueryParams(urlparse(url).query).get("at")
        sha = key[1]
        if sha in {"main", "refs/heads/main"}:
            return httpx.Response(400, json={"errors": [{"message": "branch not allowed"}]})
        if key[0] in binary_paths:
            return httpx.Response(200, content=b"\x89PNG\r\n\x00binary", headers={"content-type": "image/png"})
        text = RAW_FILES.get(key) if isinstance(raw, dict) else None
        if text is None:
            return httpx.Response(404, json={"errors": [{"message": "file not found"}]})
        return httpx.Response(200, content=text.encode(), headers={"content-type": "text/plain"})
    if "/commits" in url:
        return httpx.Response(200, json=page(COMPARISON_COMMITS))
    if "/changes" in url:
        return httpx.Response(200, json=page(COMPARISON_CHANGES))
    if url.rstrip("/").endswith("/pull-requests/42"):
        return httpx.Response(200, json=OPEN_PR)
    return httpx.Response(404, json={"errors": [{"message": "not found"}]})


@pytest.mark.asyncio
async def test_merge_base_and_raw_file_use_commit_shas():
    seen_at: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "/raw/" in str(request.url):
            seen_at.append(request.url.params["at"])
        return _comparison_handler(request)

    client = _client(handler)
    merge_base = await client.get_pull_request_merge_base("DEV", "payments", 42)
    raw = await client.get_raw_file("DEV", "payments", CLIENT_PATH, at=HEAD_SHA)
    await client.aclose()
    assert merge_base["id"] == MERGE_BASE_SHA
    assert raw.content == AFTER_CLIENT
    assert seen_at == [HEAD_SHA]


@pytest.mark.asyncio
async def test_raw_file_rejects_branch_names():
    client = _client(_comparison_handler)
    with pytest.raises(BitbucketError) as exc:
        await client.get_raw_file("DEV", "payments", CLIENT_PATH, at="main")
    await client.aclose()
    assert exc.value.status_code == 422
    assert "SHA" in exc.value.message


@pytest.mark.asyncio
async def test_raw_file_marks_binary_and_too_large():
    def handler(request: httpx.Request) -> httpx.Response:
        if "/raw/" in str(request.url) and BINARY_PATH in unquote(str(request.url)):
            return httpx.Response(200, content=b"\x89PNG\r\n\x00", headers={"content-type": "image/png"})
        if "/raw/" in str(request.url):
            return httpx.Response(200, content=b"x" * 2048, headers={"content-type": "text/plain"})
        return _comparison_handler(request)

    client = _client(handler, max_file_bytes=1024)
    binary = await client.get_raw_file("DEV", "payments", BINARY_PATH, at=HEAD_SHA)
    large = await client.get_raw_file("DEV", "payments", CLIENT_PATH, at=HEAD_SHA)
    await client.aclose()
    assert binary.binary is True
    assert binary.content is None
    assert large.too_large is True
    assert large.content is None


@pytest.mark.asyncio
async def test_comparison_covers_add_modify_delete_and_rename():
    client = _client(_comparison_handler)
    from app.services.comparison import build_comparison, build_file_comparison

    summary = await build_comparison(client, "DEV", "payments", 42)
    modified = await build_file_comparison(
        client,
        "DEV",
        "payments",
        42,
        path=CLIENT_PATH,
        src_path=None,
        change_type="MODIFY",
        base_sha=summary.base.sha,
        head_sha=summary.head.sha,
    )
    added = await build_file_comparison(
        client,
        "DEV",
        "payments",
        42,
        path=SECRETS_PATH,
        src_path=None,
        change_type="ADD",
        base_sha=summary.base.sha,
        head_sha=summary.head.sha,
    )
    deleted = await build_file_comparison(
        client,
        "DEV",
        "payments",
        42,
        path=DELETED_PATH,
        src_path=None,
        change_type="DELETE",
        base_sha=summary.base.sha,
        head_sha=summary.head.sha,
    )
    renamed = await build_file_comparison(
        client,
        "DEV",
        "payments",
        42,
        path=RENAME_DEST,
        src_path=RENAME_SRC,
        change_type="MOVE",
        base_sha=summary.base.sha,
        head_sha=summary.head.sha,
    )
    await client.aclose()

    assert summary.base.sha == MERGE_BASE_SHA
    assert summary.head.sha == HEAD_SHA
    assert summary.target.sha == TARGET_SHA
    assert summary.commit_count == 2
    types = {item.path: item.change_type for item in summary.files}
    assert types[CLIENT_PATH] == "MODIFY"
    assert types[SECRETS_PATH] == "ADD"
    assert types[DELETED_PATH] == "DELETE"
    assert types[RENAME_DEST] == "MOVE"
    assert modified.before.content == BEFORE_CLIENT
    assert modified.after.content == AFTER_CLIENT
    assert modified.additions == 1
    assert modified.deletions == 1
    assert modified.before_lines == [12]
    assert modified.after_lines == [12]
    assert added.before.missing is True
    assert added.after.content == AFTER_SECRETS
    assert deleted.after.missing is True
    assert deleted.before.content == BEFORE_DELETED
    assert renamed.before.content == BEFORE_RENAME
    assert renamed.after.content == AFTER_RENAME
    assert TOKEN not in str(summary.model_dump())


@pytest.mark.asyncio
async def test_comparison_falls_back_to_oldest_commit_parent():
    def handler(request: httpx.Request) -> httpx.Response:
        return _comparison_handler(request, merge_base=None)

    client = _client(handler)
    from app.services.comparison import build_comparison

    summary = await build_comparison(client, "DEV", "payments", 42)
    await client.aclose()
    assert summary.base.sha == MERGE_BASE_SHA
    assert summary.head.sha == HEAD_SHA


@pytest.mark.asyncio
async def test_truncated_diff_is_flagged():
    def handler(request: httpx.Request) -> httpx.Response:
        return _comparison_handler(request, diff=TRUNCATED_DIFF)

    client = _client(handler)
    from app.services.comparison import build_comparison

    summary = await build_comparison(client, "DEV", "payments", 42)
    await client.aclose()
    assert summary.truncated_diff is True
    assert summary.files[0].truncated_diff is True


def test_parse_diff_stats_reads_changed_line_numbers():
    additions, deletions, before_lines, after_lines, binary, truncated = parse_diff_stats(
        PR_DIFF, CLIENT_PATH
    )
    assert additions == 1
    assert deletions == 1
    assert before_lines == [12]
    assert after_lines == [12]
    assert binary is False
    assert truncated is False
    _, _, _, _, binary_flag, _ = parse_diff_stats(PR_DIFF, BINARY_PATH)
    assert binary_flag is True


@pytest.fixture
def override_bitbucket():
    client = _client(_comparison_handler)
    app.dependency_overrides[get_bitbucket_client] = lambda: client
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_comparison_api(client, override_bitbucket):
    resp = await client.get("/api/bitbucket/projects/DEV/repos/payments/pull-requests/42/comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert data["base"]["sha"] == MERGE_BASE_SHA
    assert data["head"]["sha"] == HEAD_SHA
    assert data["commit_count"] == 2
    assert {item["change_type"] for item in data["files"]} == {"MODIFY", "ADD", "DELETE", "MOVE"}
    assert TOKEN not in str(data)


@pytest.mark.asyncio
async def test_file_comparison_api_locks_revisions(client, override_bitbucket):
    resp = await client.get(
        "/api/bitbucket/projects/DEV/repos/payments/pull-requests/42/comparison/file",
        params={
            "path": CLIENT_PATH,
            "changeType": "MODIFY",
            "base": MERGE_BASE_SHA,
            "head": HEAD_SHA,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["before"]["content"] == BEFORE_CLIENT
    assert data["after"]["content"] == AFTER_CLIENT
    assert data["before"]["revision"] == MERGE_BASE_SHA
    assert data["after"]["revision"] == HEAD_SHA
    assert data["additions"] == 1
    assert data["deletions"] == 1


@pytest.mark.asyncio
async def test_file_comparison_api_rejects_branch_names(client, override_bitbucket):
    resp = await client.get(
        "/api/bitbucket/projects/DEV/repos/payments/pull-requests/42/comparison/file",
        params={"path": CLIENT_PATH, "base": "main", "head": HEAD_SHA},
    )
    assert resp.status_code == 422
