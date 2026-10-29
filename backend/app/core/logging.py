"""Structured logging configuration."""

import logging
import sys

from app.core.config import settings
from app.core.secrets import redact_secrets


class CredentialRedactingFilter(logging.Filter):
    """Strip Bearer/Basic tokens from log records before they hit a handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        extras = (settings.bitbucket_token, settings.bamboo_token)
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg, *extras)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: redact_secrets(val, *extras) if isinstance(val, str) else val
                    for key, val in record.args.items()
                }
            else:
                record.args = tuple(
                    redact_secrets(arg, *extras) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.backend_log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    redact = CredentialRedactingFilter()
    logging.getLogger().addFilter(redact)
    for handler in logging.getLogger().handlers:
        handler.addFilter(redact)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
