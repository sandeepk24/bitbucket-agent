import type { BitbucketPullRequest, PullRequestState } from "@/types/api";

export const PR_STATES: PullRequestState[] = ["OPEN", "MERGED", "DECLINED", "ALL"];

export function matchesPullRequest(pr: BitbucketPullRequest, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }
  const haystack = [
    String(pr.id),
    pr.title,
    pr.author?.display_name,
    pr.author?.name,
    pr.source_branch,
    pr.destination_branch,
    ...pr.reviewers.map((reviewer) => reviewer.user.display_name),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(needle);
}

export function formatEpoch(ms: number | null | undefined): string {
  if (!ms) {
    return "—";
  }
  return new Date(ms).toLocaleString();
}
