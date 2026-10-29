"""Bitbucket Data Center discovery endpoints."""

import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_bitbucket_client
from app.providers.bitbucket.client import BitbucketClient
from app.schemas.bitbucket import (
    BitbucketHealthResponse,
    BitbucketProjectListResponse,
    BitbucketRepoListResponse,
    project_from_rest,
    repo_from_rest,
)
from app.schemas.pull_requests import (
    BitbucketPullRequestDetailResponse,
    BitbucketPullRequestListResponse,
    change_from_rest,
    commit_from_rest,
    pull_request_from_rest,
)

router = APIRouter(prefix="/api/bitbucket", tags=["bitbucket"])

BitbucketDep = Annotated[BitbucketClient, Depends(get_bitbucket_client)]
ProjectKeyPath = Annotated[str, Path(alias="projectKey", min_length=1, max_length=128)]
RepoSlugPath = Annotated[str, Path(alias="repositorySlug", min_length=1, max_length=128)]
PullRequestIdPath = Annotated[int, Path(alias="pullRequestId", ge=1)]
PrStateQuery = Annotated[
    Literal["OPEN", "MERGED", "DECLINED", "ALL"],
    Query(description="Bitbucket PR state filter. Defaults to OPEN."),
]


@router.get("/health", response_model=BitbucketHealthResponse)
async def bitbucket_health(client: BitbucketDep) -> BitbucketHealthResponse:
    return BitbucketHealthResponse.model_validate(await client.health())


@router.get("/projects", response_model=BitbucketProjectListResponse)
async def list_projects(client: BitbucketDep) -> BitbucketProjectListResponse:
    items = [project_from_rest(raw) for raw in await client.list_projects()]
    return BitbucketProjectListResponse(count=len(items), items=items)


@router.get("/projects/{projectKey}/repos", response_model=BitbucketRepoListResponse)
async def list_project_repos(
    project_key: ProjectKeyPath,
    client: BitbucketDep,
) -> BitbucketRepoListResponse:
    items = [repo_from_rest(raw) for raw in await client.list_repos(project_key)]
    return BitbucketRepoListResponse(project_key=project_key, count=len(items), items=items)


@router.get(
    "/projects/{projectKey}/repos/{repositorySlug}/pull-requests",
    response_model=BitbucketPullRequestListResponse,
)
async def list_pull_requests(
    project_key: ProjectKeyPath,
    repo_slug: RepoSlugPath,
    client: BitbucketDep,
    state: PrStateQuery = "OPEN",
) -> BitbucketPullRequestListResponse:
    items = [
        pull_request_from_rest(raw)
        for raw in await client.list_pull_requests(project_key, repo_slug, state=state)
    ]
    return BitbucketPullRequestListResponse(
        project_key=project_key,
        repo_slug=repo_slug,
        state=state,
        count=len(items),
        items=items,
    )


@router.get(
    "/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}",
    response_model=BitbucketPullRequestDetailResponse,
)
async def get_pull_request(
    project_key: ProjectKeyPath,
    repo_slug: RepoSlugPath,
    pull_request_id: PullRequestIdPath,
    client: BitbucketDep,
) -> BitbucketPullRequestDetailResponse:
    raw_pr, raw_commits, raw_changes = await asyncio.gather(
        client.get_pull_request(project_key, repo_slug, pull_request_id),
        client.list_pull_request_commits(project_key, repo_slug, pull_request_id),
        client.list_pull_request_changes(project_key, repo_slug, pull_request_id),
    )
    return BitbucketPullRequestDetailResponse(
        pull_request=pull_request_from_rest(raw_pr),
        commits=[commit_from_rest(raw) for raw in raw_commits],
        changes=[change_from_rest(raw) for raw in raw_changes],
    )
