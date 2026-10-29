import { Link, useParams } from "react-router-dom";
import { ArrowLeft, GitPullRequest } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/common/Badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { Spinner } from "@/components/common/Spinner";
import { PullRequestStateBadge } from "@/components/bitbucket/PullRequestStateBadge";
import { useBitbucketPullRequestDetail } from "@/api/queries";
import { formatEpoch } from "@/lib/pull-requests";

export function PullRequestDetail() {
  const { projectKey, repositorySlug, pullRequestId } = useParams();
  const detail = useBitbucketPullRequestDetail(projectKey, repositorySlug, pullRequestId);
  const pr = detail.data?.pull_request;
  const listHref = `/pull-requests?project=${encodeURIComponent(projectKey ?? "")}&repo=${encodeURIComponent(repositorySlug ?? "")}`;

  return (
    <div className="space-y-6">
      <Link
        to={listHref}
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to pull requests
      </Link>

      {detail.isLoading ? (
        <Spinner />
      ) : detail.error ? (
        <EmptyState
          icon={GitPullRequest}
          title="Could not load this pull request"
          description={detail.error instanceof Error ? detail.error.message : "Bitbucket returned an error."}
        />
      ) : !pr ? (
        <EmptyState
          icon={GitPullRequest}
          title="Pull request not found"
          description="The ID may be wrong, or the token cannot see this repository."
        />
      ) : (
        <>
          <PageHeader
            title={`#${pr.id} ${pr.title}`}
            description={`${projectKey}/${repositorySlug} · ${pr.source_branch} → ${pr.destination_branch}`}
          >
            <PullRequestStateBadge state={pr.state} />
          </PageHeader>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Author</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                <p className="font-medium">{pr.author?.display_name ?? "—"}</p>
                <p className="text-muted-foreground">{pr.author?.email ?? pr.author?.name}</p>
                <p className="text-xs text-muted-foreground">Created {formatEpoch(pr.created_date)}</p>
                <p className="text-xs text-muted-foreground">Updated {formatEpoch(pr.updated_date)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Branches</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>
                  <span className="text-muted-foreground">Source</span>{" "}
                  <span className="font-medium">{pr.source_branch}</span>
                </p>
                <p>
                  <span className="text-muted-foreground">Destination</span>{" "}
                  <span className="font-medium">{pr.destination_branch}</span>
                </p>
                {pr.source_commit && (
                  <p className="font-mono text-xs text-muted-foreground">{pr.source_commit.slice(0, 12)}</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Reviewers</CardTitle>
                <CardDescription>
                  {pr.approved_count} of {pr.reviewer_count} approved
                </CardDescription>
              </CardHeader>
              <CardContent>
                {pr.reviewers.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No reviewers assigned.</p>
                ) : (
                  <ul className="space-y-2">
                    {pr.reviewers.map((reviewer) => (
                      <li key={reviewer.user.name} className="flex items-center justify-between gap-2 text-sm">
                        <span>{reviewer.user.display_name}</span>
                        <Badge
                          variant={
                            reviewer.status === "APPROVED"
                              ? "success"
                              : reviewer.status === "NEEDS_WORK"
                                ? "warning"
                                : "outline"
                          }
                        >
                          {reviewer.status.replaceAll("_", " ").toLowerCase()}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          {pr.description && (
            <Card>
              <CardHeader>
                <CardTitle>Description</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm text-muted-foreground">{pr.description}</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Commits</CardTitle>
              <CardDescription>{detail.data?.commits.length ?? 0} on this pull request</CardDescription>
            </CardHeader>
            <CardContent>
              {(detail.data?.commits.length ?? 0) === 0 ? (
                <p className="text-sm text-muted-foreground">No commits returned for this pull request.</p>
              ) : (
                <ul className="divide-y divide-border">
                  {detail.data?.commits.map((commit) => (
                    <li key={commit.id} className="py-3">
                      <p className="font-mono text-xs text-primary">{commit.display_id}</p>
                      <p className="text-sm">{commit.message.split("\n")[0]}</p>
                      <p className="text-xs text-muted-foreground">
                        {commit.author_name ?? "Unknown author"} · {formatEpoch(commit.author_timestamp)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Changed files</CardTitle>
              <CardDescription>{detail.data?.changes.length ?? 0} paths</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto p-0">
              {(detail.data?.changes.length ?? 0) === 0 ? (
                <p className="p-6 text-sm text-muted-foreground">No file changes returned.</p>
              ) : (
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-border text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Change</th>
                      <th className="px-4 py-3 font-medium">Path</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.data?.changes.map((change) => (
                      <tr key={change.path} className="border-b border-border last:border-0">
                        <td className="px-4 py-3">
                          <Badge variant={change.change_type === "DELETE" ? "destructive" : "outline"}>
                            {change.change_type.toLowerCase()}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">
                          {change.src_path ? `${change.src_path} → ${change.path}` : change.path}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
