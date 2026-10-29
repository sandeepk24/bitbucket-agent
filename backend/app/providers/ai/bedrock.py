"""Amazon Bedrock adapter — configuration only in this milestone."""

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.ai.base import AINotImplementedError

logger = get_logger(__name__)


class BedrockProvider:
    name = "bedrock"

    async def is_available(self) -> bool:
        configured = settings.bedrock_configured
        logger.debug("Bedrock configured=%s region=%s", configured, settings.aws_region)
        return configured

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        raise AINotImplementedError(
            "Amazon Bedrock inference is not implemented in Milestone 1 "
            f"(prompt_chars={len(prompt)}, system_set={system is not None})."
        )
