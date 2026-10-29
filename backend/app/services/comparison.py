"""Build a before/after comparison from immutable Bitbucket commit SHAs."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.errors import BitbucketError
from app.providers.bitbucket.files import RawFile, require_commit_sha
from app.schemas.comparison import (
    ComparisonFileSummary,
    ComparisonRevision,
    FileRevisionContent,
    PullRequestComparisonResponse,
    PullRequestFileComparisonResponse,
    parse_diff_stats,
)
from app.schemas.pull_requests import _path_to_string

logger = get_logger(__name__)

_EMPTY_AFTER = frozenset({"DELETE"})
_EMPTY_BEFORE = frozenset({"ADD"})


async def build_comparison(
    client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    pull_request_id: int,
) -> PullRequestComparisonResponse:
    pr = await client.get_pull_request(project_key, repo_slug, pull_request_id)
    head_sha = _ref_commit(pr.get("fromRef"), role="head")
    target_sha = _ref_commit(pr.get("toRef"), role="target")
    commits, changes = await asyncio.gather(
        client.list_pull_request_commits(project_key, repo_slug, pull_request_id),
        client.list_pull_request_changes(project_key, repo_slug, pull_request_id),
    )
    base_sha, base_display = await _resolve_base(
        client, project_key, repo_slug, pull_request_id, commits, target_sha
    )

    try:
        diff_payload = await client.get_pull_request_diff(
            project_key,
            repo_slug,
            pull_request_id,
            since_id=base_sha,
            until_id=head_sha,
        )
    except BitbucketError:
        logger.warning("PR diff unavailable; file stats will be empty")
        diff_payload = {}

    truncated_diff = bool(diff_payload.get("truncated"))
    files = [_summarize_file(change, diff_payload) for change in changes]
    return PullRequestComparisonResponse(
        project_key=project_key,
        repo_slug=repo_slug,
        pull_request_id=pull_request_id,
        base=ComparisonRevision(sha=base_sha, display_id=base_display, role="base"),
        head=ComparisonRevision(sha=head_sha, display_id=head_sha[:12], role="head"),
        target=ComparisonRevision(sha=target_sha, display_id=target_sha[:12], role="target"),
        commit_count=len(commits),
        truncated_diff=truncated_diff,
        files=files,
    )


async def build_file_comparison(
    client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    pull_request_id: int,
    *,
    path: str,
    src_path: str | None,
    change_type: str,
    base_sha: str,
    head_sha: str,
) -> PullRequestFileComparisonResponse:
    before_path = src_path or path
    after_path = path
    change = (change_type or "MODIFY").upper()
    base_sha = require_commit_sha(base_sha)
    head_sha = require_commit_sha(head_sha)

    before_raw, after_raw, diff_payload = await asyncio.gather(
        _revision_or_empty(
            client,
            project_key,
            repo_slug,
            before_path,
            base_sha,
            skip=change in _EMPTY_BEFORE,
        ),
        _revision_or_empty(
            client,
            project_key,
            repo_slug,
            after_path,
            head_sha,
            skip=change in _EMPTY_AFTER,
        ),
        _safe_file_diff(
            client,
            project_key,
            repo_slug,
            pull_request_id,
            path=path,
            src_path=src_path,
            base_sha=base_sha,
            head_sha=head_sha,
        ),
    )
    additions, deletions, before_lines, after_lines, binary, truncated = parse_diff_stats(
        diff_payload, path, src_path
    )
    before = _to_content(before_raw)
    after = _to_content(after_raw)
    if binary:
        before = before.model_copy(update={"binary": True, "content": None})
        after = after.model_copy(update={"binary": True, "content": None})
    return PullRequestFileComparisonResponse(
        path=path,
        src_path=src_path,
        change_type=change,
        base_sha=base_sha,
        head_sha=head_sha,
        additions=additions,
        deletions=deletions,
        before_lines=before_lines,
        after_lines=after_lines,
        truncated_diff=truncated,
        before=before,
        after=after,
    )


async def _resolve_base(
    client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    pull_request_id: int,
    commits: list[dict[str, Any]],
    target_sha: str,
) -> tuple[str, str | None]:
    try:
        merge_base = await client.get_pull_request_merge_base(
            project_key, repo_slug, pull_request_id
        )
        sha = require_commit_sha(str(merge_base["id"]))
        return sha, str(merge_base.get("displayId") or sha[:12])
    except BitbucketError:
        logger.info("merge-base endpoint unavailable; using oldest PR commit parent")
    if commits:
        oldest = commits[-1]
        parents = oldest.get("parents") if isinstance(oldest.get("parents"), list) else []
        if parents and isinstance(parents[0], dict) and parents[0].get("id"):
            sha = require_commit_sha(str(parents[0]["id"]))
            return sha, str(parents[0].get("displayId") or sha[:12])
    return require_commit_sha(target_sha), target_sha[:12]


def _ref_commit(ref: Any, *, role: str) -> str:
    if not isinstance(ref, dict) or not ref.get("latestCommit"):
        raise BitbucketError(f"Pull request {role} revision is missing")
    return require_commit_sha(str(ref["latestCommit"]))


def _summarize_file(change: dict[str, Any], diff_payload: dict[str, Any]) -> ComparisonFileSummary:
    path = _path_to_string(change.get("path"))
    src_path = _path_to_string(change.get("srcPath")) or None
    additions, deletions, before_lines, after_lines, binary, truncated = parse_diff_stats(
        diff_payload, path, src_path
    )
    hunks_available = True
    for diff in diff_payload.get("diffs") or []:
        if not isinstance(diff, dict):
            continue
        dest = _path_to_string(diff.get("destination"))
        src = _path_to_string(diff.get("source"))
        if dest == path or src == path or (src_path and src == src_path):
            hunks_available = isinstance(diff.get("hunks"), list)
            truncated = truncated or bool(diff.get("truncated"))
    return ComparisonFileSummary(
        path=path or "(unknown)",
        src_path=src_path,
        change_type=str(change.get("type") or "MODIFY"),
        additions=additions,
        deletions=deletions,
        before_lines=before_lines,
        after_lines=after_lines,
        binary=binary or str(change.get("nodeType") or "").upper() == "BINARY",
        truncated_diff=truncated,
        hunks_available=hunks_available,
    )


async def _revision_or_empty(
    client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    path: str,
    revision: str,
    *,
    skip: bool,
) -> RawFile:
    if skip:
        return RawFile(path=path, revision=revision, content="", size=0, missing=True)
    return await client.get_raw_file(project_key, repo_slug, path, at=revision)


async def _safe_file_diff(
    client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    pull_request_id: int,
    *,
    path: str,
    src_path: str | None,
    base_sha: str,
    head_sha: str,
) -> dict[str, Any]:
    try:
        return await client.get_pull_request_diff(
            project_key,
            repo_slug,
            pull_request_id,
            path=path,
            src_path=src_path,
            since_id=base_sha,
            until_id=head_sha,
        )
    except BitbucketError:
        return {}


def _to_content(raw: RawFile) -> FileRevisionContent:
    hide = raw.binary or raw.too_large
    return FileRevisionContent(
        path=raw.path,
        revision=raw.revision,
        content=None if hide else (raw.content if raw.content is not None else ""),
        size=raw.size,
        binary=raw.binary,
        too_large=raw.too_large,
        missing=raw.missing,
        truncated=raw.truncated,
    )
