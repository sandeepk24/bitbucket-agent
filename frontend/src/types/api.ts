export interface HealthResponse {
  status: string;
  version: string;
  bitbucket_configured: boolean;
  bamboo_configured: boolean;
  ai_provider: string;
  bedrock_configured: boolean;
  strands_configured: boolean;
}

export interface ReadyResponse {
  status: string;
}

export interface AppSettings {
  app_name: string;
  app_version: string;
  bitbucket_base_url: string;
  bitbucket_workspace: string;
  bitbucket_configured: boolean;
  bamboo_base_url: string;
  bamboo_configured: boolean;
  aws_region: string;
  ai_provider: string;
  bedrock_enabled: boolean;
  bedrock_model_id: string;
  bedrock_configured: boolean;
  strands_enabled: boolean;
  strands_configured: boolean;
}
