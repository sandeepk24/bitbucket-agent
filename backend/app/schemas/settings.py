"""Non-secret settings exposed to the UI."""

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    bitbucket_base_url: str
    bitbucket_workspace: str
    bitbucket_configured: bool
    bamboo_base_url: str
    bamboo_configured: bool
    aws_region: str
    ai_provider: str
    bedrock_enabled: bool
    bedrock_model_id: str
    bedrock_configured: bool
    strands_enabled: bool
    strands_configured: bool
