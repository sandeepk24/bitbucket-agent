import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type {
  AppSettings,
  BitbucketHealth,
  BitbucketProjectList,
  BitbucketRepoList,
  HealthResponse,
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
