"""Bitbucket client stub. No REST calls in this milestone."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BitbucketClient:
    """Reports configuration presence only. Token values are never logged."""

    def is_configured(self) -> bool:
        configured = settings.bitbucket_configured
        logger.debug(
            "Bitbucket configured=%s host=%s workspace=%s",
            configured,
            settings.bitbucket_base_url,
            settings.bitbucket_workspace or "(unset)",
        )
        return configured
