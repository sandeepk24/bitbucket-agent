"""Select an AI provider from configuration."""

from app.core.config import settings
from app.providers.ai.base import AIProvider
from app.providers.ai.bedrock import BedrockProvider
from app.providers.ai.strands import StrandsProvider


def get_ai_provider(name: str | None = None) -> AIProvider:
    selected = (name or settings.ai_provider).strip().lower()
    if selected == "strands":
        return StrandsProvider()
    return BedrockProvider()
