"""Response models for Bitbucket Data Center discovery APIs."""

from typing import Any

from pydantic import BaseModel, Field


class BitbucketHealthResponse(BaseModel):
    configured: bool
    reachable: bool
    authenticated: bool
    base_url: str | None = None
    display_name: str | None = None
    version: str | None = None
    compatible: bool = False


class BitbucketProject(BaseModel):
    key: str
    id: int | None = None
    name: str
    public: bool = False
    type: str | None = None
    description: str | None = None


class BitbucketRepo(BaseModel):
    slug: str
    id: int | None = None
    name: str
    scm_id: str | None = Field(default=None, validation_alias="scmId")
    state: str | None = None
    public: bool = False
    project_key: str | None = None
    clone_http: str | None = None

    model_config = {"populate_by_name": True}


class BitbucketProjectListResponse(BaseModel):
    count: int
    items: list[BitbucketProject]


class BitbucketRepoListResponse(BaseModel):
    project_key: str
    count: int
    items: list[BitbucketRepo]


def project_from_rest(raw: dict[str, Any]) -> BitbucketProject:
    return BitbucketProject(
        key=str(raw.get("key") or ""),
        id=raw.get("id") if isinstance(raw.get("id"), int) else None,
        name=str(raw.get("name") or raw.get("key") or ""),
        public=bool(raw.get("public", False)),
        type=raw.get("type"),
        description=raw.get("description"),
    )


def repo_from_rest(raw: dict[str, Any]) -> BitbucketRepo:
    project = raw.get("project") if isinstance(raw.get("project"), dict) else {}
    clone_http = _http_clone_url(raw)
    return BitbucketRepo.model_validate(
        {
            "slug": str(raw.get("slug") or ""),
            "id": raw.get("id") if isinstance(raw.get("id"), int) else None,
            "name": str(raw.get("name") or raw.get("slug") or ""),
            "scmId": raw.get("scmId"),
            "state": raw.get("state"),
            "public": bool(raw.get("public", False)),
            "project_key": project.get("key"),
            "clone_http": clone_http,
        }
    )


def _http_clone_url(raw: dict[str, Any]) -> str | None:
    links = raw.get("links")
    if not isinstance(links, dict):
        return None
    clones = links.get("clone")
    if not isinstance(clones, list):
        return None
    http_url = None
    for entry in clones:
        if not isinstance(entry, dict):
            continue
        href = entry.get("href")
        name = str(entry.get("name") or "").lower()
        if isinstance(href, str) and name in {"http", "https"}:
            return href
        if isinstance(href, str) and href.startswith("http"):
            http_url = href
    return http_url
