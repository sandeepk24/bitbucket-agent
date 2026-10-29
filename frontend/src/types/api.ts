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

export interface BitbucketHealth {
  configured: boolean;
  reachable: boolean;
  authenticated: boolean;
  base_url: string | null;
  display_name: string | null;
  version: string | null;
  compatible: boolean;
}

export interface BitbucketProject {
  key: string;
  id: number | null;
  name: string;
  public: boolean;
  type: string | null;
  description: string | null;
}

export interface BitbucketRepo {
  slug: string;
  id: number | null;
  name: string;
  scm_id: string | null;
  state: string | null;
  public: boolean;
  project_key: string | null;
  clone_http: string | null;
}

export interface BitbucketProjectList {
  count: number;
  items: BitbucketProject[];
}

export interface BitbucketRepoList {
  project_key: string;
  count: number;
  items: BitbucketRepo[];
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
