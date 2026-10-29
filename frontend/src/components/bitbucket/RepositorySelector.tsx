import { useBitbucketProjects, useBitbucketRepos } from "@/api/queries";
import { cn } from "@/lib/utils";

interface RepositorySelectorProps {
  projectKey: string | null;
  repoSlug: string | null;
  onChange: (projectKey: string | null, repoSlug: string | null) => void;
  disabled?: boolean;
}

const selectClass =
  "h-9 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50";

export function RepositorySelector({
  projectKey,
  repoSlug,
  onChange,
  disabled = false,
}: RepositorySelectorProps) {
  const projects = useBitbucketProjects(!disabled);
  const repos = useBitbucketRepos(disabled ? null : projectKey);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <label className="block text-sm">
        <span className="mb-1 block text-muted-foreground">Project</span>
        <select
          className={cn(selectClass)}
          disabled={disabled || projects.isLoading}
          value={projectKey ?? ""}
          onChange={(event) => {
            const next = event.target.value || null;
            onChange(next, null);
          }}
        >
          <option value="">{projects.isLoading ? "Loading projects…" : "Select a project"}</option>
          {(projects.data?.items ?? []).map((project) => (
            <option key={project.key} value={project.key}>
              {project.key} — {project.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-muted-foreground">Repository</span>
        <select
          className={cn(selectClass)}
          disabled={disabled || !projectKey || repos.isLoading}
          value={repoSlug ?? ""}
          onChange={(event) => onChange(projectKey, event.target.value || null)}
        >
          <option value="">
            {!projectKey
              ? "Select a project first"
              : repos.isLoading
                ? "Loading repositories…"
                : "Select a repository"}
          </option>
          {(repos.data?.items ?? []).map((repo) => (
            <option key={repo.slug} value={repo.slug}>
              {repo.name}
            </option>
          ))}
        </select>
      </label>
      {projects.error && (
        <p className="text-sm text-destructive sm:col-span-2">
          {projects.error instanceof Error ? projects.error.message : "Could not load projects"}
        </p>
      )}
      {repos.error && (
        <p className="text-sm text-destructive sm:col-span-2">
          {repos.error instanceof Error ? repos.error.message : "Could not load repositories"}
        </p>
      )}
    </div>
  );
}
