"""PR deep analysis against mocked Bitbucket payloads and AI providers."""

from __future__ import annotations

from urllib.parse import unquote

import httpx
import pytest

from app.api.deps import get_ai_provider_dep, get_bitbucket_client
from app.main import app
from app.providers.ai.base import AINotImplementedError
from app.services.analysis import analyze_pull_request
from app.services.static_review import scan_file
from tests.fixtures.bitbucket_comparison import (
    BINARY_PATH,
    COMPARISON_CHANGES,
    DELETED_PATH,
    HEAD_SHA,
    LOGIN_AFTER,
    LOGIN_PATH,
    MERGE_BASE_SHA,
    RENAME_DEST,
)
from tests.fixtures.bitbucket_prs import page
from tests.test_bitbucket_comparison import TOKEN, _client, _comparison_handler

LOGIN_CHANGE = {
    "type": "ADD",
    "nodeType": "FILE",
    "path": {"toString": LOGIN_PATH, "name": "login.py"},
}


class FakeProvider:
    name = "bedrock"

    def __init__(self, *, available: bool = True, result: str | None = None, error: Exception | None = None):
        self._available = available
        self._result = result
        self._error = error

    async def is_available(self) -> bool:
        return self._available

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        if self._error:
            raise self._error
        return self._result or "{}"


def _analysis_handler(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "/changes" in url:
        return httpx.Response(200, json=page([*COMPARISON_CHANGES, LOGIN_CHANGE]))
    if "/raw/" in url and LOGIN_PATH in unquote(url):
        return httpx.Response(200, content=LOGIN_AFTER.encode(), headers={"content-type": "text/plain"})
    return _comparison_handler(request)


def test_scan_file_flags_hardcoded_secret_and_eval():
    findings = scan_file(
        path=LOGIN_PATH,
        src_path=None,
        change_type="ADD",
        before=None,
        after=LOGIN_AFTER,
        base_sha=MERGE_BASE_SHA,
        head_sha=HEAD_SHA,
    )
    titles = {item.title for item in findings}
    assert "Hardcoded credential in source" in titles
    assert "Dynamic eval of untrusted input" in titles
    confirmed = [item for item in findings if item.kind == "confirmed"]
    assert confirmed[0].after_lines
    assert confirmed[0].evidence[0].line == 1
    assert "hunter2" in (confirmed[0].evidence[0].quote or "")


def test_scan_file_marks_deleted_auth_as_hypothetical():
    findings = scan_file(
        path=DELETED_PATH,
        src_path=None,
        change_type="DELETE",
        before="def login():\n    print(token)\n",
        after=None,
        base_sha=MERGE_BASE_SHA,
        head_sha=HEAD_SHA,
    )
    kinds = {(item.kind, item.source, item.title) for item in findings}
    assert ("confirmed", "static", "Secret value written to logs or stdout") in kinds
    assert any(item.kind == "hypothetical" and "Security-sensitive" in item.title for item in findings)


@pytest.mark.asyncio
async def test_analysis_groups_static_findings_and_skips_binary():
    client = _client(_analysis_handler)
    report = await analyze_pull_request(client, FakeProvider(available=False), "DEV", "payments", 42)
    await client.aclose()
    assert report.base_sha == MERGE_BASE_SHA
    assert report.head_sha == HEAD_SHA
    assert report.commit_count == 2
    assert report.model.available is False
    assert report.model.error
    assert any(item.reason == "binary" and item.path == BINARY_PATH for item in report.unsupported_files)
    titles = {item.title for item in report.findings}
    assert "Hardcoded credential in source" in titles
    assert any(item.kind == "confirmed" and item.source == "static" for item in report.findings)
    assert any(item.kind == "hypothetical" for item in report.findings)
    assert any(item.path == RENAME_DEST for item in report.findings)
    assert TOKEN not in str(report.model_dump())
    assert {stage.id for stage in report.progress} >= {"static-review", "model-inference", "assemble"}


@pytest.mark.asyncio
async def test_analysis_records_model_error_when_inference_is_not_wired():
    client = _client(_analysis_handler)
    report = await analyze_pull_request(
        client,
        FakeProvider(available=True, error=AINotImplementedError("Amazon Bedrock inference is not implemented")),
        "DEV",
        "payments",
        42,
    )
    await client.aclose()
    assert report.status == "partial"
    assert report.model.available is True
    assert report.model.used is False
    assert "not implemented" in (report.model.error or "").lower()
    assert any(stage.status == "error" for stage in report.progress if stage.id == "model-inference")
    assert report.findings  # static findings remain


@pytest.mark.asyncio
async def test_analysis_merges_model_findings():
    payload = """
    {
      "summary": "Token handling is safer, but login still embeds a password.",
      "production_impact": "A hardcoded password can unlock production if this ships.",
      "findings": [
        {
          "title": "Login bypass if password leaks",
          "severity": "high",
          "kind": "hypothetical",
          "path": "backend/app/api/login.py",
          "after_lines": [1],
          "evidence": ["password assigned in source"],
          "risk": "Anyone with the repo can authenticate as this user.",
          "recommended_fix": "Load credentials from a secret manager.",
          "production_impact": "Account takeover in production."
        }
      ]
    }
    """
    client = _client(_analysis_handler)
    report = await analyze_pull_request(
        client, FakeProvider(available=True, result=payload), "DEV", "payments", 42
    )
    await client.aclose()
    assert report.model.used is True
    assert report.model.error is None
    assert "Token handling is safer" in report.summary
    model_hits = [item for item in report.findings if item.source == "model"]
    assert model_hits[0].kind == "hypothetical"
    assert model_hits[0].after_lines == [1]
    assert model_hits[0].path == LOGIN_PATH


@pytest.fixture
def override_services():
    client = _client(_analysis_handler)
    app.dependency_overrides[get_bitbucket_client] = lambda: client
    app.dependency_overrides[get_ai_provider_dep] = lambda: FakeProvider(available=False)
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analysis_api(client, override_services):
    resp = await client.get("/api/bitbucket/projects/DEV/repos/payments/pull-requests/42/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pull_request_id"] == 42
    assert data["base_sha"] == MERGE_BASE_SHA
    assert data["head_sha"] == HEAD_SHA
    assert data["findings"]
    assert data["components"]
    assert any(item["path"] == LOGIN_PATH for item in data["files"])
    assert TOKEN not in str(data)
    assert "hunter2" in str(data)  # evidence quote from static review of the fixture
