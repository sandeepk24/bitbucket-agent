"""Bitbucket Data Center discovery endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_bitbucket_client
from app.providers.bitbucket.client import BitbucketClient
from app.schemas.bitbucket import (
    BitbucketHealthResponse,
    BitbucketProjectListResponse,
    BitbucketRepoListResponse,
    project_from_rest,
    repo_from_rest,
)

router = APIRouter(prefix="/api/bitbucket", tags=["bitbucket"])

BitbucketDep = Annotated[BitbucketClient, Depends(get_bitbucket_client)]
ProjectKeyPath = Annotated[str, Path(alias="projectKey", min_length=1, max_length=128)]


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
