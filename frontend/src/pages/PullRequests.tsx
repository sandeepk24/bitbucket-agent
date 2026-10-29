import { Link, useSearchParams } from "react-router-dom";
import { GitPullRequest, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardContent } from "@/components/common/Card";
import { Spinner } from "@/components/common/Spinner";
import { Button } from "@/components/common/Button";
import { RepositorySelector } from "@/components/bitbucket/RepositorySelector";
import { PullRequestStateBadge } from "@/components/bitbucket/PullRequestStateBadge";
import { useBitbucketHealth, useBitbucketPullRequests } from "@/api/queries";
import { PR_STATES, formatEpoch, matchesPullRequest } from "@/lib/pull-requests";
import { cn } from "@/lib/utils";
import type { PullRequestState } from "@/types/api";

function asState(value: string | null): PullRequestState {
  return PR_STATES.includes(value as PullRequestState) ? (value as PullRequestState) : "OPEN";
}

export function PullRequests() {
  const health = useBitbucketHealth();
  const [params, setParams] = useSearchParams();
  const projectKey = params.get("project");
  const repoSlug = params.get("repo");
  const state = asState(params.get("state"));
  const query = params.get("q") ?? "";
  const configured = Boolean(health.data?.configured);
  const authenticated = Boolean(health.data?.authenticated);
  const prs = useBitbucketPullRequests(projectKey, repoSlug, state);
  const visible = (prs.data?.items ?? []).filter((item) => matchesPullRequest(item, query));

  function update(next: Record<string, string | null>) {
    const merged = new URLSearchParams(params);
    for (const [key, value] of Object.entries(next)) {
      if (value) {
        merged.set(key, value);
      } else {
        merged.delete(key);
      }
    }
    setParams(merged);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pull Requests"
        description="Open, merged, and declined pull requests from a Bitbucket Data Center repository."
      />

      {health.isLoading ? (
        <Spinner />
      ) : !configured ? (
        <EmptyState
          icon={GitPullRequest}
          title="Bitbucket is not configured"
          description="Set BITBUCKET_BASE_URL and BITBUCKET_TOKEN to list pull requests. Tokens stay on the server."
        />
      ) : !health.data?.reachable ? (
        <EmptyState
          icon={GitPullRequest}
          title="Bitbucket is unreachable"
          description="The backend could not reach the Data Center instance."
        />
      ) : !authenticated ? (
        <EmptyState
          icon={GitPullRequest}
          title="Bitbucket rejected the access token"
          description="Check the HTTP access token and its repository permissions."
        />
      ) : (
        <>
          <Card>
            <CardContent className="space-y-4 p-6">
              <RepositorySelector
                projectKey={projectKey}
                repoSlug={repoSlug}
                onChange={(project, repo) =>
                  update({ project, repo, q: query || null })
                }
              />
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-wrap gap-2">
                  {PR_STATES.map((item) => (
                    <Button
                      key={item}
                      size="sm"
                      variant={state === item ? "default" : "outline"}
                      onClick={() => update({ state: item })}
                    >
                      {item === "ALL" ? "All" : item.charAt(0) + item.slice(1).toLowerCase()}
                    </Button>
                  ))}
                </div>
                <label className="relative block w-full lg:max-w-sm">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    value={query}
                    onChange={(event) => update({ q: event.target.value || null })}
                    placeholder="Search by ID, title, author, or branch"
                    className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </label>
              </div>
            </CardContent>
          </Card>

          {!projectKey || !repoSlug ? (
            <EmptyState
              icon={GitPullRequest}
              title="Select a repository"
              description="Choose a project and repository to load pull requests from Bitbucket Data Center."
            />
          ) : prs.isLoading ? (
            <Spinner />
          ) : prs.error ? (
            <p className="text-sm text-destructive">
              {prs.error instanceof Error ? prs.error.message : "Could not load pull requests"}
            </p>
          ) : (prs.data?.items.length ?? 0) === 0 ? (
            <EmptyState
              icon={GitPullRequest}
              title={`No ${state === "ALL" ? "" : state.toLowerCase() + " "}pull requests`}
              description={`${projectKey}/${repoSlug} has no pull requests in this filter.`}
            />
          ) : visible.length === 0 ? (
            <EmptyState
              icon={GitPullRequest}
              title="No matching pull requests"
              description="Try a different search term. Filtering happens in the table and does not hide other states."
            />
          ) : (
            <Card>
              <CardContent className="overflow-x-auto p-0">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-border text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">ID</th>
                      <th className="px-4 py-3 font-medium">Title</th>
                      <th className="px-4 py-3 font-medium">Author</th>
                      <th className="px-4 py-3 font-medium">Branches</th>
                      <th className="px-4 py-3 font-medium">Reviewers</th>
                      <th className="px-4 py-3 font-medium">State</th>
                      <th className="px-4 py-3 font-medium">Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((pr) => (
                      <tr key={pr.id} className="border-b border-border last:border-0 hover:bg-accent/40">
                        <td className="px-4 py-3 font-medium">
                          <Link
                            to={`/pull-requests/${encodeURIComponent(projectKey)}/${encodeURIComponent(repoSlug)}/${pr.id}`}
                            className={cn("text-primary hover:underline")}
                          >
                            #{pr.id}
                          </Link>
                        </td>
                        <td className="max-w-sm px-4 py-3">
                          <Link
                            to={`/pull-requests/${encodeURIComponent(projectKey)}/${encodeURIComponent(repoSlug)}/${pr.id}`}
                            className="hover:underline"
                          >
                            {pr.title}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {pr.author?.display_name ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {pr.source_branch} → {pr.destination_branch}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {pr.approved_count}/{pr.reviewer_count} approved
                        </td>
                        <td className="px-4 py-3">
                          <PullRequestStateBadge state={pr.state} />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                          {formatEpoch(pr.updated_date)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
