"""Bamboo client stub. No REST calls in this milestone."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BambooClient:
    """Reports configuration presence only. Token values are never logged."""

    def is_configured(self) -> bool:
        configured = settings.bamboo_configured
        logger.debug("Bamboo configured=%s host=%s", configured, settings.bamboo_base_url or "(unset)")
        return configured
