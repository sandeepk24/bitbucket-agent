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

export type PullRequestState = "OPEN" | "MERGED" | "DECLINED" | "ALL";

export interface BitbucketUser {
  name: string;
  display_name: string;
  email: string | null;
  slug: string | null;
}

export interface BitbucketParticipant {
  user: BitbucketUser;
  role: string;
  approved: boolean;
  status: string;
}

export interface BitbucketPullRequest {
  id: number;
  version: number | null;
  title: string;
  description: string | null;
  state: string;
  open: boolean;
  closed: boolean;
  created_date: number | null;
  updated_date: number | null;
  html_url: string | null;
  author: BitbucketUser | null;
  reviewers: BitbucketParticipant[];
  source_branch: string;
  destination_branch: string;
  source_commit: string | null;
  destination_commit: string | null;
  approved_count: number;
  reviewer_count: number;
}

export interface BitbucketCommit {
  id: string;
  display_id: string;
  message: string;
  author_name: string | null;
  author_email: string | null;
  author_timestamp: number | null;
}

export interface BitbucketFileChange {
  path: string;
  src_path: string | null;
  change_type: string;
  node_type: string | null;
  executable: boolean;
}

export interface BitbucketPullRequestList {
  project_key: string;
  repo_slug: string;
  state: string;
  count: number;
  items: BitbucketPullRequest[];
}

export interface BitbucketPullRequestDetail {
  pull_request: BitbucketPullRequest;
  commits: BitbucketCommit[];
  changes: BitbucketFileChange[];
}

export interface ComparisonRevision {
  sha: string;
  display_id: string | null;
  role: string;
}

export interface FileRevisionContent {
  path: string;
  revision: string;
  content: string | null;
  size: number;
  binary: boolean;
  too_large: boolean;
  missing: boolean;
  truncated: boolean;
}

export interface ComparisonFileSummary {
  path: string;
  src_path: string | null;
  change_type: string;
  additions: number;
  deletions: number;
  before_lines: number[];
  after_lines: number[];
  binary: boolean;
  truncated_diff: boolean;
  hunks_available: boolean;
}

export interface PullRequestComparison {
  project_key: string;
  repo_slug: string;
  pull_request_id: number;
  base: ComparisonRevision;
  head: ComparisonRevision;
  target: ComparisonRevision | null;
  commit_count: number;
  truncated_diff: boolean;
  files: ComparisonFileSummary[];
}

export interface PullRequestFileComparison {
  path: string;
  src_path: string | null;
  change_type: string;
  base_sha: string;
  head_sha: string;
  additions: number;
  deletions: number;
  before_lines: number[];
  after_lines: number[];
  truncated_diff: boolean;
  before: FileRevisionContent;
  after: FileRevisionContent;
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
