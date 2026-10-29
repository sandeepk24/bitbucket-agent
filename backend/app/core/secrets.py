"""Helpers that keep credentials out of logs and error payloads."""

from __future__ import annotations

import re
from typing import Any

_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-+=]+")
_BASIC = re.compile(r"(?i)(basic\s+)[A-Za-z0-9+/=]+")
_AUTH_HEADER = re.compile(r"(?i)(authorization\s*[:=]\s*)([^\s,;]+)")


def redact_secrets(value: Any, *extra: str) -> Any:
    """Replace known secret material with asterisks. Never returns the original token."""
    if not isinstance(value, str):
        return value
    redacted = _BEARER.sub(r"\1***", value)
    redacted = _BASIC.sub(r"\1***", redacted)
    redacted = _AUTH_HEADER.sub(r"\1***", redacted)
    for secret in extra:
        if secret and secret in redacted:
            redacted = redacted.replace(secret, "***")
    return redacted
