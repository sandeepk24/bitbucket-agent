"""Connection settings for a Bitbucket Data Center instance."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, settings


def normalize_base_url(url: str) -> str:
    """Accept an instance root and strip accidental REST suffixes."""
    cleaned = url.strip().rstrip("/")
    for suffix in ("/rest/api/latest", "/rest/api/1.0"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].rstrip("/")
    return cleaned


@dataclass(frozen=True, slots=True)
class BitbucketConfig:
    base_url: str
    token: str
    username: str = ""
    timeout: float = 30.0
    connect_timeout: float = 5.0
    max_retries: int = 3
    page_limit: int = 100
    max_pages: int = 50
    verify_ssl: bool = True
    max_file_bytes: int = 1_048_576

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    @property
    def api_root(self) -> str:
        return f"{self.base_url}/rest/api/latest"

    @classmethod
    def from_settings(cls, source: Settings | None = None) -> BitbucketConfig:
        cfg = source or settings
        return cls(
            base_url=normalize_base_url(cfg.bitbucket_base_url),
            token=cfg.bitbucket_token.strip(),
            username=cfg.bitbucket_username.strip(),
            timeout=float(cfg.bitbucket_api_timeout),
            connect_timeout=cfg.bitbucket_connect_timeout,
            max_retries=cfg.bitbucket_max_retries,
            page_limit=cfg.bitbucket_page_limit,
            max_pages=cfg.bitbucket_max_pages,
            verify_ssl=cfg.bitbucket_verify_ssl,
            max_file_bytes=cfg.bitbucket_max_file_bytes,
        )
