"""Bitbucket Data Center REST client (10.2.x).

Official endpoints used:

- GET /rest/api/latest/application-properties
- GET /rest/api/latest/projects
- GET /rest/api/latest/projects/{projectKey}/repos
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/commits
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/changes
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/merge-base
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/diff[/{path}]
- GET /rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/raw/{path}?at={sha}

Auth follows Bitbucket 10.2 HTTP access tokens: Bearer when no username is
set, otherwise Basic username:token. Tokens are never logged.
"""

from __future__ import annotations

import asyncio
import base64
import random
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx

from app.core.logging import get_logger
from app.core.secrets import redact_secrets
from app.providers.bitbucket.config import BitbucketConfig
from app.providers.bitbucket.errors import (
    BitbucketAuthError,
    BitbucketError,
    BitbucketNotConfiguredError,
    BitbucketNotFoundError,
    BitbucketUnavailableError,
)
from app.providers.bitbucket.files import RawFile, is_binary_payload, require_commit_sha

logger = get_logger(__name__)

_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})
_RETRYABLE_EXC = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)
_PROJECT_KEY = re.compile(r"^~?[A-Za-z0-9._-]+$")
_REPO_SLUG = re.compile(r"^[A-Za-z0-9._-]+$")
_PR_STATES = frozenset({"OPEN", "MERGED", "DECLINED", "ALL"})
_COMPATIBLE_PREFIX = "10.2."


class BitbucketClient:
    """Reusable async client with pooling, timeouts, retries, and pagination."""

    def __init__(
        self,
        config: BitbucketConfig | None = None,
        *,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config or BitbucketConfig.from_settings()
        self._owned_client = client is None
        self._client = client or httpx.AsyncClient(
            transport=transport,
            headers={
                "Accept": "application/json",
                "User-Agent": "BitbucketAgent/0.1.0",
            },
            timeout=httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.timeout,
                write=min(self._config.timeout, 15.0),
                pool=self._config.connect_timeout,
            ),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=30.0,
            ),
            verify=self._config.verify_ssl,
            follow_redirects=False,
        )

    @property
    def config(self) -> BitbucketConfig:
        return self._config

    def is_configured(self) -> bool:
        configured = self._config.configured
        logger.debug(
            "Bitbucket configured=%s host=%s auth=%s",
            configured,
            self._config.base_url or "(unset)",
            "basic" if self._config.username else "bearer",
        )
        return configured

    async def aclose(self) -> None:
        if self._owned_client:
            await self._client.aclose()

    async def get_application_properties(self) -> dict[str, Any]:
        payload = await self._get_json("application-properties")
        if not isinstance(payload, dict):
            raise BitbucketError("Unexpected application-properties payload")
        return payload

    async def list_projects(self) -> list[dict[str, Any]]:
        return await self._paginate("projects")

    async def list_repos(self, project_key: str) -> list[dict[str, Any]]:
        key = _validate_project_key(project_key)
        return await self._paginate(f"projects/{_seg(key)}/repos")

    async def list_pull_requests(
        self,
        project_key: str,
        repo_slug: str,
        *,
        state: str = "OPEN",
    ) -> list[dict[str, Any]]:
        key = _validate_project_key(project_key)
        slug = _validate_repo_slug(repo_slug)
        return await self._paginate(
            f"projects/{_seg(key)}/repos/{_seg(slug)}/pull-requests",
            params={"state": _validate_pr_state(state), "withAttributes": "true"},
        )

    async def get_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pull_request_id: int,
    ) -> dict[str, Any]:
        path = _pr_path(project_key, repo_slug, pull_request_id)
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise BitbucketError("Unexpected pull request payload")
        return payload

    async def list_pull_request_commits(
        self,
        project_key: str,
        repo_slug: str,
        pull_request_id: int,
    ) -> list[dict[str, Any]]:
        return await self._paginate(_pr_path(project_key, repo_slug, pull_request_id) + "/commits")

    async def list_pull_request_changes(
        self,
        project_key: str,
        repo_slug: str,
        pull_request_id: int,
    ) -> list[dict[str, Any]]:
        return await self._paginate(_pr_path(project_key, repo_slug, pull_request_id) + "/changes")

    async def get_pull_request_merge_base(
        self,
        project_key: str,
        repo_slug: str,
        pull_request_id: int,
    ) -> dict[str, Any]:
        payload = await self._get_json(_pr_path(project_key, repo_slug, pull_request_id) + "/merge-base")
        if not isinstance(payload, dict) or not payload.get("id"):
            raise BitbucketError("Unexpected merge-base payload")
        return payload

    async def get_pull_request_diff(
        self,
        project_key: str,
        repo_slug: str,
        pull_request_id: int,
        *,
        path: str | None = None,
        src_path: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
    ) -> dict[str, Any]:
        diff_path = _pr_path(project_key, repo_slug, pull_request_id) + "/diff"
        if path:
            diff_path = f"{diff_path}/{_file_path(path)}"
        params: dict[str, Any] = {"withComments": "false"}
        if src_path:
            params["srcPath"] = src_path
        if since_id:
            params["sinceId"] = require_commit_sha(since_id)
        if until_id:
            params["untilId"] = require_commit_sha(until_id)
        payload = await self._get_json(diff_path, params=params)
        if not isinstance(payload, dict):
            raise BitbucketError("Unexpected pull request diff payload")
        return payload

    async def get_raw_file(
        self,
        project_key: str,
        repo_slug: str,
        path: str,
        *,
        at: str,
    ) -> RawFile:
        """Read a file at an immutable commit SHA. Branch names are rejected."""
        key = _validate_project_key(project_key)
        slug = _validate_repo_slug(repo_slug)
        revision = require_commit_sha(at)
        file_path = _file_path(path)
        encoded = f"projects/{_seg(key)}/repos/{_seg(slug)}/raw/{file_path}"
        url = f"{self._config.api_root}/{encoded}"
        headers = {**self._auth_headers(), "Accept": "*/*"}
        delay = 0.25
        last_error: Exception | None = None

        if not self._config.configured:
            raise BitbucketNotConfiguredError()

        for attempt in range(self._config.max_retries + 1):
            try:
                async with self._client.stream(
                    "GET",
                    url,
                    headers=headers,
                    params={"at": revision},
                ) as response:
                    if response.status_code in _RETRYABLE_STATUS and attempt < self._config.max_retries:
                        await response.aclose()
                        retry_after = _retry_after_seconds(response)
                        await asyncio.sleep(retry_after if retry_after is not None else _jitter(delay))
                        delay = min(delay * 2, 4.0)
                        continue
                    if response.status_code >= 400:
                        await response.aread()
                        try:
                            self._raise_for_status(response, encoded)
                        except BitbucketNotFoundError:
                            return RawFile(path=path, revision=revision, content=None, size=0, missing=True)
                    return await _read_raw_file(response, path, revision, self._config.max_file_bytes)
            except _RETRYABLE_EXC as exc:
                last_error = exc
                if attempt >= self._config.max_retries:
                    logger.warning(
                        "Bitbucket GET %s failed after retries: %s",
                        encoded,
                        type(exc).__name__,
                    )
                    raise BitbucketUnavailableError() from exc
                await asyncio.sleep(_jitter(delay))
                delay = min(delay * 2, 4.0)

        raise BitbucketUnavailableError() from last_error

    async def health(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "configured": self.is_configured(),
            "reachable": False,
            "authenticated": False,
            "base_url": self._config.base_url or None,
            "display_name": None,
            "version": None,
            "compatible": False,
        }
        if not result["configured"]:
            return result
        try:
            props = await self.get_application_properties()
        except BitbucketAuthError:
            result["reachable"] = True
            result["authenticated"] = False
            return result
        except BitbucketError:
            return result

        version = str(props.get("version") or "")
        result.update(
            {
                "reachable": True,
                "authenticated": True,
                "display_name": props.get("displayName"),
                "version": version or None,
                "compatible": version.startswith(_COMPATIBLE_PREFIX),
            }
        )
        return result

    async def _paginate(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        start = 0
        extra = dict(params or {})
        for _page in range(self._config.max_pages):
            payload = await self._get_json(
                path,
                params={"start": start, "limit": self._config.page_limit, **extra},
            )
            page_values = payload.get("values") if isinstance(payload, dict) else None
            if not isinstance(page_values, list):
                raise BitbucketError("Bitbucket page payload was missing values")
            values.extend(item for item in page_values if isinstance(item, dict))
            if payload.get("isLastPage", True):
                return values
            next_start = payload.get("nextPageStart")
            if not isinstance(next_start, int):
                return values
            start = next_start
        raise BitbucketError("Bitbucket pagination exceeded the configured page cap")

    async def _get_json(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        response = await self._request("GET", path, params=params)
        try:
            return response.json()
        except ValueError as exc:
            raise BitbucketError("Bitbucket returned a non-JSON body") from exc

    async def _request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        if not self._config.configured:
            raise BitbucketNotConfiguredError()

        url = f"{self._config.api_root}/{path.lstrip('/')}"
        headers = {**self._auth_headers(), **(headers or {})}
        delay = 0.25
        last_error: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                )
            except _RETRYABLE_EXC as exc:
                last_error = exc
                if attempt >= self._config.max_retries:
                    logger.warning(
                        "Bitbucket %s %s failed after retries: %s",
                        method,
                        path,
                        type(exc).__name__,
                    )
                    raise BitbucketUnavailableError() from exc
                await asyncio.sleep(_jitter(delay))
                delay = min(delay * 2, 4.0)
                continue

            logger.debug("Bitbucket %s %s -> %s", method, path, response.status_code)

            if response.status_code in _RETRYABLE_STATUS and attempt < self._config.max_retries:
                retry_after = _retry_after_seconds(response)
                await asyncio.sleep(retry_after if retry_after is not None else _jitter(delay))
                delay = min(delay * 2, 4.0)
                continue

            return self._raise_for_status(response, path)

        raise BitbucketUnavailableError() from last_error

    def _auth_headers(self) -> dict[str, str]:
        if self._config.username:
            blob = f"{self._config.username}:{self._config.token}".encode()
            encoded = base64.b64encode(blob).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        return {"Authorization": f"Bearer {self._config.token}"}

    def _raise_for_status(self, response: httpx.Response, path: str) -> httpx.Response:
        status = response.status_code
        if status < 400:
            return response

        detail = _safe_error_detail(response, self._config.token)
        logger.warning("Bitbucket %s returned %s (%s)", path, status, detail)

        if status in {401, 403}:
            raise BitbucketAuthError()
        if status == 404:
            raise BitbucketNotFoundError(f"Bitbucket resource not found: {path}")
        if status >= 500:
            raise BitbucketUnavailableError()
        raise BitbucketError(f"Bitbucket request failed with status {status}")


def _validate_project_key(project_key: str) -> str:
    key = project_key.strip()
    if not _PROJECT_KEY.fullmatch(key):
        raise BitbucketError("Invalid Bitbucket project key", status_code=422)
    return key


def _validate_repo_slug(repo_slug: str) -> str:
    slug = repo_slug.strip()
    if not _REPO_SLUG.fullmatch(slug):
        raise BitbucketError("Invalid Bitbucket repository slug", status_code=422)
    return slug


def _validate_pr_state(state: str) -> str:
    value = state.strip().upper()
    if value not in _PR_STATES:
        raise BitbucketError("Invalid pull request state", status_code=422)
    return value


def _validate_pr_id(pull_request_id: int) -> int:
    if pull_request_id < 1:
        raise BitbucketError("Invalid pull request id", status_code=422)
    return pull_request_id


def _seg(value: str) -> str:
    return quote(value, safe="~._-")


def _pr_path(project_key: str, repo_slug: str, pull_request_id: int) -> str:
    key = _validate_project_key(project_key)
    slug = _validate_repo_slug(repo_slug)
    pr_id = _validate_pr_id(pull_request_id)
    return f"projects/{_seg(key)}/repos/{_seg(slug)}/pull-requests/{pr_id}"


def _file_path(path: str) -> str:
    cleaned = path.strip().lstrip("/")
    parts = [part for part in cleaned.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise BitbucketError("Invalid file path", status_code=422)
    return "/".join(quote(part, safe="._-") for part in parts)


async def _read_raw_file(response: httpx.Response, path: str, revision: str, max_bytes: int) -> RawFile:
    size_header = response.headers.get("content-length")
    declared = int(size_header) if size_header and size_header.isdigit() else None
    if declared is not None and declared > max_bytes:
        await response.aclose()
        return RawFile(path=path, revision=revision, content=None, size=declared, too_large=True)

    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > max_bytes:
            await response.aclose()
            return RawFile(path=path, revision=revision, content=None, size=total, too_large=True)
        chunks.append(chunk)
    body = b"".join(chunks)
    if is_binary_payload(body, response.headers.get("content-type")):
        return RawFile(path=path, revision=revision, content=None, size=len(body), binary=True)
    truncated = "truncated" in (response.headers.get("x-bitbucket-truncated") or "").lower()
    return RawFile(
        path=path,
        revision=revision,
        content=body.decode("utf-8", errors="replace"),
        size=len(body),
        truncated=truncated,
    )


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None


def _jitter(delay: float) -> float:
    return delay + random.uniform(0, delay / 4)


def _safe_error_detail(response: httpx.Response, token: str) -> str:
    try:
        payload = response.json()
        message = payload.get("message") or payload.get("errors")
        text = str(message)[:200] if message else response.reason_phrase
    except ValueError:
        text = response.reason_phrase
    return redact_secrets(text, token)
