"""Shared FastAPI dependencies."""

from fastapi import Request

from app.providers.ai.base import AIProvider
from app.providers.ai.factory import get_ai_provider
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig


def get_bitbucket_client(request: Request) -> BitbucketClient:
    client = getattr(request.app.state, "bitbucket", None)
    if client is None:
        client = BitbucketClient(BitbucketConfig.from_settings())
        request.app.state.bitbucket = client
    return client


def get_ai_provider_dep() -> AIProvider:
    return get_ai_provider()
