"""Typed models mapped from Bitbucket Data Center pull-request REST payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BitbucketUser(BaseModel):
    name: str
    display_name: str
    email: str | None = None
    slug: str | None = None


class BitbucketParticipant(BaseModel):
    user: BitbucketUser
    role: str
    approved: bool = False
    status: str = "UNAPPROVED"


class BitbucketRef(BaseModel):
    id: str | None = None
    display_id: str
    latest_commit: str | None = None
    repository_slug: str | None = None
    project_key: str | None = None


class BitbucketPullRequest(BaseModel):
    id: int
    version: int | None = None
    title: str
    description: str | None = None
    state: str
    open: bool = False
    closed: bool = False
    created_date: int | None = None
    updated_date: int | None = None
    html_url: str | None = None
    author: BitbucketUser | None = None
    reviewers: list[BitbucketParticipant] = Field(default_factory=list)
    source_branch: str
    destination_branch: str
    source_commit: str | None = None
    destination_commit: str | None = None
    approved_count: int = 0
    reviewer_count: int = 0


class BitbucketCommit(BaseModel):
    id: str
    display_id: str
    message: str
    author_name: str | None = None
    author_email: str | None = None
    author_timestamp: int | None = None


class BitbucketFileChange(BaseModel):
    path: str
    src_path: str | None = None
    change_type: str
    node_type: str | None = None
    executable: bool = False


class BitbucketPullRequestListResponse(BaseModel):
    project_key: str
    repo_slug: str
    state: str
    count: int
    items: list[BitbucketPullRequest]


class BitbucketPullRequestDetailResponse(BaseModel):
    pull_request: BitbucketPullRequest
    commits: list[BitbucketCommit]
    changes: list[BitbucketFileChange]


def user_from_rest(raw: dict[str, Any] | None) -> BitbucketUser | None:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or raw.get("slug") or "")
    if not name:
        return None
    return BitbucketUser(
        name=name,
        display_name=str(raw.get("displayName") or name),
        email=raw.get("emailAddress"),
        slug=raw.get("slug"),
    )


def participant_from_rest(raw: dict[str, Any]) -> BitbucketParticipant | None:
    user = user_from_rest(raw.get("user") if isinstance(raw.get("user"), dict) else raw)
    if user is None:
        return None
    return BitbucketParticipant(
        user=user,
        role=str(raw.get("role") or "REVIEWER"),
        approved=bool(raw.get("approved", False)),
        status=str(raw.get("status") or ("APPROVED" if raw.get("approved") else "UNAPPROVED")),
    )


def ref_from_rest(raw: Any) -> BitbucketRef | None:
    if not isinstance(raw, dict):
        return None
    repo = raw.get("repository") if isinstance(raw.get("repository"), dict) else {}
    project = repo.get("project") if isinstance(repo.get("project"), dict) else {}
    display = str(raw.get("displayId") or raw.get("id") or "")
    if not display:
        return None
    return BitbucketRef(
        id=raw.get("id"),
        display_id=display,
        latest_commit=raw.get("latestCommit"),
        repository_slug=repo.get("slug"),
        project_key=project.get("key"),
    )


def pull_request_from_rest(raw: dict[str, Any]) -> BitbucketPullRequest:
    from_ref = ref_from_rest(raw.get("fromRef"))
    to_ref = ref_from_rest(raw.get("toRef"))
    author_block = raw.get("author") if isinstance(raw.get("author"), dict) else {}
    author = user_from_rest(author_block.get("user") if isinstance(author_block.get("user"), dict) else None)
    reviewers: list[BitbucketParticipant] = []
    for item in raw.get("reviewers") or []:
        if isinstance(item, dict):
            participant = participant_from_rest(item)
            if participant is not None:
                reviewers.append(participant)
    pr_id = raw.get("id")
    if not isinstance(pr_id, int):
        raise ValueError("Pull request payload is missing a numeric id")
    return BitbucketPullRequest(
        id=pr_id,
        version=raw.get("version") if isinstance(raw.get("version"), int) else None,
        title=str(raw.get("title") or f"Pull request {pr_id}"),
        description=raw.get("description"),
        state=str(raw.get("state") or "OPEN"),
        open=bool(raw.get("open", False)),
        closed=bool(raw.get("closed", False)),
        created_date=raw.get("createdDate") if isinstance(raw.get("createdDate"), int) else None,
        updated_date=raw.get("updatedDate") if isinstance(raw.get("updatedDate"), int) else None,
        html_url=_self_href(raw),
        author=author,
        reviewers=reviewers,
        source_branch=from_ref.display_id if from_ref else "",
        destination_branch=to_ref.display_id if to_ref else "",
        source_commit=from_ref.latest_commit if from_ref else None,
        destination_commit=to_ref.latest_commit if to_ref else None,
        approved_count=sum(1 for reviewer in reviewers if reviewer.approved or reviewer.status == "APPROVED"),
        reviewer_count=len(reviewers),
    )


def commit_from_rest(raw: dict[str, Any]) -> BitbucketCommit:
    author = raw.get("author") if isinstance(raw.get("author"), dict) else {}
    commit_id = str(raw.get("id") or "")
    return BitbucketCommit(
        id=commit_id,
        display_id=str(raw.get("displayId") or commit_id[:7]),
        message=str(raw.get("message") or ""),
        author_name=author.get("name") or author.get("displayName"),
        author_email=author.get("emailAddress"),
        author_timestamp=raw.get("authorTimestamp") if isinstance(raw.get("authorTimestamp"), int) else None,
    )


def change_from_rest(raw: dict[str, Any]) -> BitbucketFileChange:
    path = _path_to_string(raw.get("path"))
    src_path = _path_to_string(raw.get("srcPath"))
    return BitbucketFileChange(
        path=path or "(unknown)",
        src_path=src_path or None,
        change_type=str(raw.get("type") or "UNKNOWN"),
        node_type=raw.get("nodeType"),
        executable=bool(raw.get("executable", False)),
    )


def _path_to_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("toString"), str):
            return value["toString"]
        name = value.get("name")
        parent = value.get("parent")
        if name and parent:
            return f"{parent}/{name}"
        if name:
            return str(name)
    return ""


def _self_href(raw: dict[str, Any]) -> str | None:
    links = raw.get("links")
    if not isinstance(links, dict):
        return None
    self_links = links.get("self")
    if isinstance(self_links, list) and self_links:
        first = self_links[0]
        if isinstance(first, dict) and isinstance(first.get("href"), str):
            return first["href"]
    return None
