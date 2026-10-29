import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type {
  AppSettings,
  BitbucketHealth,
  BitbucketProjectList,
  BitbucketPullRequestDetail,
  BitbucketPullRequestList,
  BitbucketRepoList,
  HealthResponse,
  PullRequestState,
} from "@/types/api";

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.get<HealthResponse>("/health"),
    refetchInterval: 15_000,
    retry: 1,
  });
}

export function useSettings() {
  return useQuery<AppSettings>({
    queryKey: ["settings"],
    queryFn: () => api.get<AppSettings>("/settings"),
  });
}

export function useBitbucketHealth() {
  return useQuery<BitbucketHealth>({
    queryKey: ["bitbucket", "health"],
    queryFn: () => api.get<BitbucketHealth>("/api/bitbucket/health"),
    retry: 1,
  });
}

export function useBitbucketProjects(enabled = true) {
  return useQuery<BitbucketProjectList>({
    queryKey: ["bitbucket", "projects"],
    queryFn: () => api.get<BitbucketProjectList>("/api/bitbucket/projects"),
    enabled,
    retry: 1,
  });
}

export function useBitbucketRepos(projectKey: string | null) {
  return useQuery<BitbucketRepoList>({
    queryKey: ["bitbucket", "repos", projectKey],
    queryFn: () =>
      api.get<BitbucketRepoList>(
        `/api/bitbucket/projects/${encodeURIComponent(projectKey ?? "")}/repos`
      ),
    enabled: Boolean(projectKey),
    retry: 1,
  });
}

export function useBitbucketPullRequests(
  projectKey: string | null,
  repoSlug: string | null,
  state: PullRequestState
) {
  return useQuery<BitbucketPullRequestList>({
    queryKey: ["bitbucket", "prs", projectKey, repoSlug, state],
    queryFn: () =>
      api.get<BitbucketPullRequestList>(
        `/api/bitbucket/projects/${encodeURIComponent(projectKey ?? "")}/repos/${encodeURIComponent(repoSlug ?? "")}/pull-requests?state=${state}`
      ),
    enabled: Boolean(projectKey && repoSlug),
    retry: 1,
  });
}

export function useBitbucketPullRequestDetail(
  projectKey: string | undefined,
  repoSlug: string | undefined,
  pullRequestId: string | undefined
) {
  return useQuery<BitbucketPullRequestDetail>({
    queryKey: ["bitbucket", "pr", projectKey, repoSlug, pullRequestId],
    queryFn: () =>
      api.get<BitbucketPullRequestDetail>(
        `/api/bitbucket/projects/${encodeURIComponent(projectKey ?? "")}/repos/${encodeURIComponent(repoSlug ?? "")}/pull-requests/${pullRequestId}`
      ),
    enabled: Boolean(projectKey && repoSlug && pullRequestId),
    retry: 1,
  });
}
