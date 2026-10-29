"""Health and readiness schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    bitbucket_configured: bool
    bamboo_configured: bool
    ai_provider: str
    bedrock_configured: bool
    strands_configured: bool


class ReadyResponse(BaseModel):
    status: str = Field(examples=["ready"])
