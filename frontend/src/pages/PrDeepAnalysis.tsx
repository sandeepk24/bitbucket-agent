import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AlertTriangle, ScanSearch, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { Spinner } from "@/components/common/Spinner";
import { RepositorySelector } from "@/components/bitbucket/RepositorySelector";
import { PullRequestComparison } from "@/components/bitbucket/PullRequestComparison";
import { AnalysisProgress } from "@/components/analysis/AnalysisProgress";
import {
  useBitbucketHealth,
  useBitbucketPullRequests,
  usePullRequestAnalysis,
} from "@/api/queries";
import {
  SEVERITIES,
  filterFindings,
  groupFindingsBySeverity,
  kindLabel,
  severityLabel,
} from "@/lib/analysis";
import { cn } from "@/lib/utils";
import type { AnalysisFinding, AnalysisSeverity } from "@/types/api";

export function PrDeepAnalysis() {
  const health = useBitbucketHealth();
  const [params, setParams] = useSearchParams();
  const projectKey = params.get("project");
  const repoSlug = params.get("repo");
  const pullRequestId = params.get("pr");
  const [severity, setSeverity] = useState<AnalysisSeverity | "all">("all");
  const [fileQuery, setFileQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const configured = Boolean(health.data?.configured);
  const prs = useBitbucketPullRequests(projectKey, repoSlug, "ALL");
  const analysis = usePullRequestAnalysis(projectKey, repoSlug, pullRequestId);
  const findings = analysis.data?.findings ?? [];
  const visible = useMemo(
    () => filterFindings(findings, severity, fileQuery),
    [findings, severity, fileQuery]
  );
  const grouped = useMemo(() => groupFindingsBySeverity(visible), [visible]);
  const selected =
    visible.find((item) => item.id === selectedId) ?? visible[0] ?? findings.find((item) => item.id === selectedId) ?? null;

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
    setSelectedId(null);
  }

  function selectFinding(finding: AnalysisFinding) {
    setSelectedId(finding.id);
    document.getElementById("pr-comparison")?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="PR Deep Analysis"
        description="SHA-locked review of diffs with confirmed static findings and hypothetical runtime risks."
      />

      {health.isLoading ? (
        <Spinner />
      ) : !configured ? (
        <EmptyState
          icon={ScanSearch}
          title="Bitbucket is not configured"
          description="Set BITBUCKET_BASE_URL and BITBUCKET_TOKEN to analyze pull requests."
        />
      ) : (
        <>
          <Card>
            <CardContent className="space-y-4 p-6">
              <RepositorySelector
                projectKey={projectKey}
                repoSlug={repoSlug}
                onChange={(project, repo) => update({ project, repo, pr: null })}
              />
              <label className="block text-sm">
                <span className="mb-1 block text-muted-foreground">Pull request</span>
                <select
                  className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                  disabled={!projectKey || !repoSlug || prs.isLoading}
                  value={pullRequestId ?? ""}
                  onChange={(event) => update({ pr: event.target.value || null })}
                >
                  <option value="">
                    {!projectKey || !repoSlug
                      ? "Select a repository first"
                      : prs.isLoading
                        ? "Loading pull requests…"
                        : "Select a pull request"}
                  </option>
                  {(prs.data?.items ?? []).map((pr) => (
                    <option key={pr.id} value={String(pr.id)}>
                      #{pr.id} {pr.title}
                    </option>
                  ))}
                </select>
              </label>
            </CardContent>
          </Card>

          {!projectKey || !repoSlug || !pullRequestId ? (
            <EmptyState
              icon={ScanSearch}
              title="Select a pull request"
              description="Choose a project, repository, and pull request to run deep analysis."
            />
          ) : analysis.isLoading || analysis.isFetching ? (
            <Card>
              <CardHeader>
                <CardTitle>Analyzing #{pullRequestId}</CardTitle>
                <CardDescription>Fetching locked revisions, scanning text files, then calling the model.</CardDescription>
              </CardHeader>
              <CardContent>
                <AnalysisProgress pending />
              </CardContent>
            </Card>
          ) : analysis.error ? (
            <EmptyState
              icon={ScanSearch}
              title="Analysis failed"
              description={analysis.error instanceof Error ? analysis.error.message : "The analysis endpoint returned an error."}
            />
          ) : !analysis.data ? (
            <EmptyState icon={ScanSearch} title="No analysis" description="Run analysis by selecting a pull request." />
          ) : (
            <AnalysisResult
              projectKey={projectKey}
              repoSlug={repoSlug}
              pullRequestId={pullRequestId}
              severity={severity}
              fileQuery={fileQuery}
              grouped={grouped}
              visibleCount={visible.length}
              selected={selected}
              onSeverity={setSeverity}
              onFileQuery={setFileQuery}
              onSelectFinding={selectFinding}
            />
          )}
        </>
      )}
    </div>
  );
}

function AnalysisResult({
  projectKey,
  repoSlug,
  pullRequestId,
  severity,
  fileQuery,
  grouped,
  visibleCount,
  selected,
  onSeverity,
  onFileQuery,
  onSelectFinding,
}: {
  projectKey: string;
  repoSlug: string;
  pullRequestId: string;
  severity: AnalysisSeverity | "all";
  fileQuery: string;
  grouped: { severity: AnalysisSeverity; items: AnalysisFinding[] }[];
  visibleCount: number;
  selected: AnalysisFinding | null;
  onSeverity: (value: AnalysisSeverity | "all") => void;
  onFileQuery: (value: string) => void;
  onSelectFinding: (finding: AnalysisFinding) => void;
}) {
  const analysis = usePullRequestAnalysis(projectKey, repoSlug, pullRequestId);
  const data = analysis.data;
  if (!data) {
    return null;
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle>
                #{data.pull_request_id} {data.title}
              </CardTitle>
              <CardDescription>
                {data.source_branch} → {data.destination_branch} · {data.commit_count} commit
                {data.commit_count === 1 ? "" : "s"} · base {data.base_sha.slice(0, 12)} → head{" "}
                {data.head_sha.slice(0, 12)}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={data.status === "complete" ? "success" : "warning"}>{data.status}</Badge>
              <Badge variant="outline">{data.model.provider}</Badge>
              <Link
                to={`/pull-requests/${encodeURIComponent(projectKey)}/${encodeURIComponent(repoSlug)}/${pullRequestId}`}
                className="text-sm text-primary hover:underline"
              >
                Open PR detail
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <AnalysisProgress stages={data.progress} />
          {data.model.error && (
            <p className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              Model error: {data.model.error} Confirmed static findings are still shown.
            </p>
          )}
          {data.unsupported_files.length > 0 && (
            <div className="rounded-md border border-border bg-secondary/40 px-3 py-2 text-sm">
              <p className="font-medium">Unsupported files</p>
              <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
                {data.unsupported_files.map((file) => (
                  <li key={`${file.path}-${file.reason}`}>
                    <span className="font-mono">{file.path}</span> · {file.reason} — {file.detail}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SummaryCard title="Overall summary" body={data.summary} />
        <SummaryCard title="Risk" body={data.risk_summary} />
        <SummaryCard title="Potential production impact" body={data.production_impact} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Changed files and components</CardTitle>
          <CardDescription>{data.files.length} paths in this pull request range</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {data.components.map((component) => (
            <button
              key={component.name}
              type="button"
              onClick={() => onFileQuery(component.name)}
              className="rounded-md border border-border bg-secondary/40 px-3 py-2 text-left text-sm hover:border-primary/40"
            >
              <span className="font-medium">{component.name}</span>
              <span className="ml-2 text-xs text-muted-foreground">
                {component.file_count} files · {component.finding_count} findings
              </span>
            </button>
          ))}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,22rem)_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Findings</CardTitle>
            <CardDescription>
              {visibleCount} of {data.findings.length} shown
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <FilterChip active={severity === "all"} onClick={() => onSeverity("all")}>
                All
              </FilterChip>
              {SEVERITIES.map((item) => (
                <FilterChip key={item} active={severity === item} onClick={() => onSeverity(item)}>
                  {severityLabel(item)}
                </FilterChip>
              ))}
            </div>
            <label className="relative block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                value={fileQuery}
                onChange={(event) => onFileQuery(event.target.value)}
                placeholder="Filter by file or component"
                className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            {grouped.length === 0 ? (
              <p className="text-sm text-muted-foreground">No findings match this filter.</p>
            ) : (
              <div className="max-h-[36rem] space-y-4 overflow-y-auto pr-1">
                {grouped.map((group) => (
                  <section key={group.severity}>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {severityLabel(group.severity)}
                    </p>
                    <ul className="space-y-2">
                      {group.items.map((finding) => (
                        <li key={finding.id}>
                          <button
                            type="button"
                            onClick={() => onSelectFinding(finding)}
                            className={cn(
                              "w-full rounded-md border border-border px-3 py-2 text-left text-sm hover:bg-accent",
                              selected?.id === finding.id && "border-primary/50 bg-accent"
                            )}
                          >
                            <span className="flex items-center justify-between gap-2">
                              <SeverityBadge severity={finding.severity} />
                              <span className="text-[11px] text-muted-foreground">
                                {finding.kind === "confirmed" ? "confirmed" : "hypothetical"}
                              </span>
                            </span>
                            <p className="mt-1 font-medium">{finding.title}</p>
                            <p className="mt-1 truncate font-mono text-xs text-muted-foreground">{finding.path}</p>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </section>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Finding detail</CardTitle>
            <CardDescription>
              {selected ? kindLabel(selected.kind, selected.source) : "Select a finding to inspect evidence."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selected ? (
              <p className="text-sm text-muted-foreground">No finding selected.</p>
            ) : (
              <div className="space-y-4 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={selected.severity} />
                  <Badge variant={selected.kind === "confirmed" ? "success" : "warning"}>
                    {kindLabel(selected.kind, selected.source)}
                  </Badge>
                </div>
                <h3 className="text-base font-semibold">{selected.title}</h3>
                <p className="font-mono text-xs text-muted-foreground">
                  {selected.src_path ? `${selected.src_path} → ${selected.path}` : selected.path}
                  {selected.after_lines.length > 0 && ` · after L${selected.after_lines.join(", ")}`}
                  {selected.before_lines.length > 0 && ` · before L${selected.before_lines.join(", ")}`}
                </p>
                <DetailBlock title="Risk" body={selected.risk} />
                <DetailBlock title="Recommended fix" body={selected.recommended_fix} />
                <DetailBlock title="Potential production impact" body={selected.production_impact} />
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Evidence</p>
                  {selected.evidence.length === 0 ? (
                    <p className="text-muted-foreground">No line-level evidence was attached.</p>
                  ) : (
                    <ul className="space-y-2">
                      {selected.evidence.map((item, index) => (
                        <li key={`${item.path}-${item.line}-${index}`} className="rounded-md bg-secondary/50 px-3 py-2">
                          <p className="font-mono text-xs text-muted-foreground">
                            {item.path}
                            {item.line ? `:${item.line}` : ""} · {item.revision.slice(0, 12)}
                          </p>
                          {item.quote && <p className="mt-1 font-mono text-xs">{item.quote}</p>}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <Button type="button" size="sm" onClick={() => onSelectFinding(selected)}>
                  Jump to changed lines
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <PullRequestComparison
        projectKey={projectKey}
        repoSlug={repoSlug}
        pullRequestId={pullRequestId}
        selectedPath={selected?.path ?? null}
        highlightBeforeLines={selected?.before_lines}
        highlightAfterLines={selected?.after_lines}
      />
    </>
  );
}

function SummaryCard({ title, body }: { title: string; body: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{body}</p>
      </CardContent>
    </Card>
  );
}

function DetailBlock({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <p className="text-muted-foreground">{body}</p>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={active ? "default" : "outline"}
      aria-pressed={active}
      aria-label={`Filter ${children}`}
      onClick={onClick}
    >
      {children}
    </Button>
  );
}

function SeverityBadge({ severity }: { severity: AnalysisSeverity }) {
  const variant =
    severity === "critical" || severity === "high"
      ? "destructive"
      : severity === "medium"
        ? "warning"
        : "outline";
  return <Badge variant={variant}>{severityLabel(severity)}</Badge>;
}
