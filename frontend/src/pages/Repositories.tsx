import { useState } from "react";
import { GitBranch } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/common/Badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { Spinner } from "@/components/common/Spinner";
import { useBitbucketHealth, useBitbucketProjects, useBitbucketRepos } from "@/api/queries";
import { cn } from "@/lib/utils";

export function Repositories() {
  const health = useBitbucketHealth();
  const configured = Boolean(health.data?.configured);
  const authenticated = Boolean(health.data?.authenticated);
  const projects = useBitbucketProjects(authenticated);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const repos = useBitbucketRepos(selectedKey);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Repositories"
        description="Projects and repositories from Bitbucket Data Center. Pull request analysis is not wired yet."
      />

      {health.isLoading ? (
        <Spinner />
      ) : !configured ? (
        <EmptyState
          icon={GitBranch}
          title="Bitbucket is not configured"
          description="Set BITBUCKET_BASE_URL and BITBUCKET_TOKEN on the backend to discover projects. Tokens stay on the server."
        />
      ) : health.data && !health.data.reachable ? (
        <EmptyState
          icon={GitBranch}
          title="Bitbucket is unreachable"
          description="The backend could not reach BITBUCKET_BASE_URL. Check the host, TLS, and network path from this service."
        />
      ) : health.data && !health.data.authenticated ? (
        <EmptyState
          icon={GitBranch}
          title="Bitbucket rejected the access token"
          description="The instance is reachable but authentication failed. Check the HTTP access token and its project permissions."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Projects</CardTitle>
              <CardDescription>
                {health.data?.version
                  ? `Bitbucket ${health.data.version}`
                  : "Connected instance"}
                {health.data?.compatible ? " · 10.2 compatible" : ""}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {projects.isLoading ? (
                <Spinner />
              ) : projects.error ? (
                <p className="text-sm text-destructive">
                  {projects.error instanceof Error ? projects.error.message : "Could not load projects"}
                </p>
              ) : (
                <ul className="space-y-1">
                  {(projects.data?.items ?? []).map((project) => (
                    <li key={project.key}>
                      <button
                        type="button"
                        onClick={() => setSelectedKey(project.key)}
                        className={cn(
                          "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors",
                          selectedKey === project.key
                            ? "bg-accent text-foreground"
                            : "hover:bg-accent/50"
                        )}
                      >
                        <span>
                          <span className="font-medium">{project.key}</span>
                          <span className="ml-2 text-muted-foreground">{project.name}</span>
                        </span>
                        {project.public && <Badge variant="outline">public</Badge>}
                      </button>
                    </li>
                  ))}
                  {projects.data?.count === 0 && (
                    <li className="px-3 py-6 text-sm text-muted-foreground">No visible projects.</li>
                  )}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Repositories</CardTitle>
              <CardDescription>
                {selectedKey ? `Project ${selectedKey}` : "Select a project"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedKey ? (
                <p className="py-8 text-sm text-muted-foreground">Choose a project to list its repositories.</p>
              ) : repos.isLoading ? (
                <Spinner />
              ) : repos.error ? (
                <p className="text-sm text-destructive">
                  {repos.error instanceof Error ? repos.error.message : "Could not load repositories"}
                </p>
              ) : (
                <ul className="divide-y divide-border">
                  {(repos.data?.items ?? []).map((repo) => (
                    <li key={repo.slug} className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm font-medium">{repo.name}</p>
                        <p className="text-xs text-muted-foreground">{repo.clone_http || repo.slug}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {repo.state && <Badge variant="outline">{repo.state}</Badge>}
                        {repo.scm_id && <Badge variant="default">{repo.scm_id}</Badge>}
                      </div>
                    </li>
                  ))}
                  {repos.data?.count === 0 && (
                    <li className="py-6 text-sm text-muted-foreground">No repositories in this project.</li>
                  )}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
