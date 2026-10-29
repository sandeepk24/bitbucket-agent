"""Credential redaction helpers."""

from app.core.secrets import redact_secrets


def test_redacts_bearer_and_basic_tokens():
    assert "***" in redact_secrets("Authorization: Bearer abcdef0123456789")
    assert "abcdef0123456789" not in redact_secrets("Authorization: Bearer abcdef0123456789")
    assert "c2VjcmV0" not in redact_secrets("Basic c2VjcmV0")


def test_redacts_explicit_secret():
    assert redact_secrets("token=hunter2 in the body", "hunter2") == "token=*** in the body"
