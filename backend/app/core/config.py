"""Application configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Bitbucket Agent"
    app_version: str = "0.1.0"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    # Bitbucket Data Center instance root, not the Cloud API host.
    # Example: https://bitbucket.example.com or https://bitbucket.example.com/bitbucket
    bitbucket_base_url: str = ""
    bitbucket_workspace: str = ""
    bitbucket_token: str = ""
    bitbucket_username: str = ""
    bitbucket_api_timeout: int = Field(default=30, ge=5, le=120)
    bitbucket_connect_timeout: float = Field(default=5.0, ge=1.0, le=30.0)
    bitbucket_max_retries: int = Field(default=3, ge=0, le=8)
    bitbucket_page_limit: int = Field(default=100, ge=1, le=1000)
    bitbucket_max_pages: int = Field(default=50, ge=1, le=200)
    bitbucket_verify_ssl: bool = True
    bitbucket_max_file_bytes: int = Field(default=1_048_576, ge=16_384, le=10_485_760)

    bamboo_base_url: str = ""
    bamboo_token: str = ""
    bamboo_api_timeout: int = Field(default=30, ge=5, le=120)

    aws_region: str = "us-east-1"
    ai_provider: str = "bedrock"
    bedrock_enabled: bool = False
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    strands_enabled: bool = False

    @property
    def bitbucket_configured(self) -> bool:
        return bool(self.bitbucket_base_url.strip() and self.bitbucket_token.strip())

    @property
    def bamboo_configured(self) -> bool:
        return bool(self.bamboo_base_url.strip() and self.bamboo_token.strip())

    @property
    def bedrock_configured(self) -> bool:
        return self.bedrock_enabled and bool(self.bedrock_model_id.strip())

    @property
    def strands_configured(self) -> bool:
        return self.strands_enabled


settings = Settings()
