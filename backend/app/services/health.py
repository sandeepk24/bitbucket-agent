"""Health and settings assembly. Does not call Bitbucket, Bamboo, or AI providers."""

from app.core.config import settings
from app.providers.ai.factory import get_ai_provider
from app.providers.bamboo.client import BambooClient
from app.providers.bitbucket.client import BitbucketClient
from app.schemas.health import HealthResponse, ReadyResponse
from app.schemas.settings import SettingsResponse


async def build_health() -> HealthResponse:
    bitbucket = BitbucketClient()
    bamboo = BambooClient()
    provider = get_ai_provider()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        bitbucket_configured=bitbucket.is_configured(),
        bamboo_configured=bamboo.is_configured(),
        ai_provider=provider.name,
        bedrock_configured=settings.bedrock_configured,
        strands_configured=settings.strands_configured,
    )


def build_ready() -> ReadyResponse:
    return ReadyResponse(status="ready")


def build_settings() -> SettingsResponse:
    return SettingsResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        bitbucket_base_url=settings.bitbucket_base_url,
        bitbucket_workspace=settings.bitbucket_workspace,
        bitbucket_configured=settings.bitbucket_configured,
        bamboo_base_url=settings.bamboo_base_url,
        bamboo_configured=settings.bamboo_configured,
        aws_region=settings.aws_region,
        ai_provider=settings.ai_provider,
        bedrock_enabled=settings.bedrock_enabled,
        bedrock_model_id=settings.bedrock_model_id,
        bedrock_configured=settings.bedrock_configured,
        strands_enabled=settings.strands_enabled,
        strands_configured=settings.strands_configured,
    )
