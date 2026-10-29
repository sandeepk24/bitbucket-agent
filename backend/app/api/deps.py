"""Shared FastAPI dependencies."""

from fastapi import Request

from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig


def get_bitbucket_client(request: Request) -> BitbucketClient:
    client = getattr(request.app.state, "bitbucket", None)
    if client is None:
        client = BitbucketClient(BitbucketConfig.from_settings())
        request.app.state.bitbucket = client
    return client
