"""PR before/after comparison models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ComparisonRevision(BaseModel):
    sha: str
    display_id: str | None = None
    role: str


class FileRevisionContent(BaseModel):
    path: str
    revision: str
    content: str | None = None
    size: int = 0
    binary: bool = False
    too_large: bool = False
    missing: bool = False
    truncated: bool = False


class ComparisonFileSummary(BaseModel):
    path: str
    src_path: str | None = None
    change_type: str
    additions: int = 0
    deletions: int = 0
    before_lines: list[int] = Field(default_factory=list)
    after_lines: list[int] = Field(default_factory=list)
    binary: bool = False
    truncated_diff: bool = False
    hunks_available: bool = True


class PullRequestComparisonResponse(BaseModel):
    project_key: str
    repo_slug: str
    pull_request_id: int
    base: ComparisonRevision
    head: ComparisonRevision
    target: ComparisonRevision | None = None
    commit_count: int = 0
    truncated_diff: bool = False
    files: list[ComparisonFileSummary]


class PullRequestFileComparisonResponse(BaseModel):
    path: str
    src_path: str | None = None
    change_type: str
    base_sha: str
    head_sha: str
    additions: int = 0
    deletions: int = 0
    before_lines: list[int] = Field(default_factory=list)
    after_lines: list[int] = Field(default_factory=list)
    truncated_diff: bool = False
    before: FileRevisionContent
    after: FileRevisionContent


def parse_diff_stats(
    diff_payload: dict[str, Any],
    path: str,
    src_path: str | None = None,
) -> tuple[int, int, list[int], list[int], bool, bool]:
    """Return additions, deletions, before lines, after lines, binary, truncated."""
    additions = 0
    deletions = 0
    before_lines: list[int] = []
    after_lines: list[int] = []
    binary = False
    truncated = bool(diff_payload.get("truncated"))
    names = {name for name in (path, src_path) if name}
    for diff in diff_payload.get("diffs") or []:
        if not isinstance(diff, dict):
            continue
        dest = _path_name(diff.get("destination"))
        src = _path_name(diff.get("source"))
        if names and dest not in names and src not in names:
            continue
        truncated = truncated or bool(diff.get("truncated"))
        hunks = diff.get("hunks")
        if hunks is None and (diff.get("binary") or dest.endswith((".png", ".jpg", ".gif", ".zip"))):
            binary = True
            continue
        if not isinstance(hunks, list):
            binary = binary or bool(diff.get("binary"))
            continue
        for hunk in hunks:
            if not isinstance(hunk, dict):
                continue
            for segment in hunk.get("segments") or []:
                if not isinstance(segment, dict):
                    continue
                seg_type = str(segment.get("type") or "")
                for line in segment.get("lines") or []:
                    if not isinstance(line, dict):
                        continue
                    if seg_type == "ADDED":
                        additions += 1
                        dest_line = line.get("destination")
                        if isinstance(dest_line, int):
                            after_lines.append(dest_line)
                    elif seg_type == "REMOVED":
                        deletions += 1
                        src_line = line.get("source")
                        if isinstance(src_line, int):
                            before_lines.append(src_line)
    return additions, deletions, before_lines, after_lines, binary, truncated


def _path_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("toString") or value.get("name") or "")
    if isinstance(value, str):
        return value
    return ""
