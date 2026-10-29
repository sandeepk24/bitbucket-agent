"""Provider stubs must not perform network I/O in this milestone."""

import pytest

from app.providers.ai.base import AINotImplementedError
from app.providers.ai.factory import get_ai_provider
from app.providers.bamboo.client import BambooClient
from app.providers.bitbucket.client import BitbucketClient


def test_bitbucket_client_unconfigured():
    assert BitbucketClient().is_configured() is False


def test_bamboo_client_unconfigured():
    assert BambooClient().is_configured() is False


def test_default_ai_provider_is_bedrock():
    provider = get_ai_provider()
    assert provider.name == "bedrock"


def test_strands_provider_selected_by_name():
    provider = get_ai_provider("strands")
    assert provider.name == "strands"


@pytest.mark.asyncio
async def test_bedrock_generate_not_implemented():
    provider = get_ai_provider("bedrock")
    assert await provider.is_available() is False
    with pytest.raises(AINotImplementedError):
        await provider.generate("hello")


@pytest.mark.asyncio
async def test_strands_generate_not_implemented():
    provider = get_ai_provider("strands")
    assert await provider.is_available() is False
    with pytest.raises(AINotImplementedError):
        await provider.generate("hello")
