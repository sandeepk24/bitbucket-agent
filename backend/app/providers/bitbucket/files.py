"""File content fetched at an immutable commit SHA."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.providers.bitbucket.errors import BitbucketError

COMMIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_BINARY_MARKERS = (b"\x00",)


@dataclass(frozen=True, slots=True)
class RawFile:
    path: str
    revision: str
    content: str | None
    size: int
    binary: bool = False
    too_large: bool = False
    missing: bool = False
    truncated: bool = False


def require_commit_sha(value: str) -> str:
    """Accept a hex commit SHA only. Branch names and refs are rejected."""
    sha = value.strip()
    if not COMMIT_SHA_RE.fullmatch(sha) or sha.startswith("refs/") or "/" in sha:
        raise BitbucketError("Revision must be a commit SHA, not a branch name", status_code=422)
    return sha


def is_binary_payload(body: bytes, content_type: str | None) -> bool:
    if any(marker in body[:8192] for marker in _BINARY_MARKERS):
        return True
    if not content_type:
        return False
    lowered = content_type.lower()
    if lowered.startswith("text/") or "json" in lowered or "xml" in lowered or "javascript" in lowered:
        return False
    return (
        "octet-stream" in lowered
        or lowered.startswith("image/")
        or lowered.startswith("audio/")
        or lowered.startswith("video/")
    )
