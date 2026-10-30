import { useMemo, useState } from "react";
import { Columns2, FileCode, List } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { Spinner } from "@/components/common/Spinner";
import { CodeDiffViewer } from "@/components/bitbucket/CodeDiffViewer";
import {
  useBitbucketPullRequestComparison,
  useBitbucketPullRequestFileComparison,
} from "@/api/queries";
import { diffBlockReason, fileLabel, formatLineNumbers, shortSha } from "@/lib/comparison";
import { cn } from "@/lib/utils";
import type { ComparisonFileSummary } from "@/types/api";

interface PullRequestComparisonProps {
  projectKey: string | undefined;
  repoSlug: string | undefined;
  pullRequestId: string | undefined;
  selectedPath?: string | null;
  onSelectedPathChange?: (path: string) => void;
  highlightBeforeLines?: number[];
  highlightAfterLines?: number[];
}

function changeVariant(changeType: string): "success" | "destructive" | "outline" | "warning" {
  if (changeType === "ADD") {
    return "success";
  }
  if (changeType === "DELETE") {
    return "destructive";
  }
  if (changeType === "MOVE" || changeType === "COPY") {
    return "warning";
  }
  return "outline";
}

export function PullRequestComparison({
  projectKey,
  repoSlug,
  pullRequestId,
  selectedPath,
  onSelectedPathChange,
  highlightBeforeLines,
  highlightAfterLines,
}: PullRequestComparisonProps) {
  const comparison = useBitbucketPullRequestComparison(projectKey, repoSlug, pullRequestId);
  const [internalPath, setInternalPath] = useState<string | null>(null);
  const [sideBySide, setSideBySide] = useState(true);
  const activePath = selectedPath ?? internalPath;

  const files = comparison.data?.files ?? [];
  const selected = useMemo<ComparisonFileSummary | null>(() => {
    if (files.length === 0) {
      return null;
    }
    return files.find((file) => file.path === activePath) ?? files[0];
  }, [files, activePath]);

  function selectPath(path: string) {
    setInternalPath(path);
    onSelectedPathChange?.(path);
  }

  const fileQuery = useBitbucketPullRequestFileComparison(
    projectKey,
    repoSlug,
    pullRequestId,
    selected,
    comparison.data?.base.sha,
    comparison.data?.head.sha
  );
  const file = fileQuery.data;
  const blockReason = file ? diffBlockReason(file) : "ready";

  return (
    <Card id="pr-comparison">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Before / after</CardTitle>
            <CardDescription>
              {comparison.data
                ? `Locked to ${shortSha(comparison.data.base.sha)} → ${shortSha(comparison.data.head.sha)} across ${comparison.data.commit_count} commit${comparison.data.commit_count === 1 ? "" : "s"}. Branch heads are not used.`
                : "File content at the pull request base and head revisions."}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={sideBySide ? "default" : "outline"}
              onClick={() => setSideBySide(true)}
            >
              <Columns2 className="h-4 w-4" />
              Side by side
            </Button>
            <Button
              type="button"
              size="sm"
              variant={!sideBySide ? "default" : "outline"}
              onClick={() => setSideBySide(false)}
            >
              <List className="h-4 w-4" />
              Inline
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {comparison.isLoading ? (
          <div className="p-6">
            <Spinner />
          </div>
        ) : comparison.error ? (
          <div className="p-6">
            <EmptyState
              icon={FileCode}
              title="Could not load this comparison"
              description={
                comparison.error instanceof Error
                  ? comparison.error.message
                  : "Bitbucket returned an error."
              }
            />
          </div>
        ) : files.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No file changes returned.</p>
        ) : (
          <div className="grid min-h-[28rem] grid-cols-1 border-t border-border lg:grid-cols-[18rem_1fr]">
            <nav className="max-h-[70vh] overflow-y-auto border-b border-border lg:border-b-0 lg:border-r" aria-label="Changed files">
              <ul>
                {files.map((item) => {
                  const active = item.path === selected?.path;
                  return (
                    <li key={item.path}>
                      <button
                        type="button"
                        onClick={() => selectPath(item.path)}
                        className={cn(
                          "flex w-full flex-col gap-1 px-4 py-3 text-left text-sm hover:bg-accent",
                          active && "bg-accent"
                        )}
                      >
                        <span className="flex items-center justify-between gap-2">
                          <Badge variant={changeVariant(item.change_type)}>
                            {item.change_type.toLowerCase()}
                          </Badge>
                          <span className="font-mono text-xs">
                            <span className="text-success">+{item.additions}</span>{" "}
                            <span className="text-destructive">-{item.deletions}</span>
                          </span>
                        </span>
                        <span className="break-all font-mono text-xs text-muted-foreground">
                          {fileLabel(item)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </nav>
            <div className="flex min-h-[28rem] flex-col">
              {selected && (
                <div className="space-y-1 border-b border-border px-4 py-3">
                  <p className="font-mono text-sm">{fileLabel(selected)}</p>
                  <p className="text-xs text-muted-foreground">
                    Before lines {formatLineNumbers(file?.before_lines ?? selected.before_lines)} · After
                    lines {formatLineNumbers(file?.after_lines ?? selected.after_lines)}
                  </p>
                  {(comparison.data?.truncated_diff || file?.truncated_diff || selected.truncated_diff) && (
                    <p className="text-xs text-warning">
                      Bitbucket truncated this diff. Line stats may be incomplete.
                    </p>
                  )}
                </div>
              )}
              <div className="min-h-[24rem] flex-1">
                {fileQuery.isLoading ? (
                  <div className="p-6">
                    <Spinner />
                  </div>
                ) : fileQuery.error ? (
                  <div className="p-6">
                    <EmptyState
                      icon={FileCode}
                      title="Could not load this file"
                      description={
                        fileQuery.error instanceof Error
                          ? fileQuery.error.message
                          : "Bitbucket returned an error."
                      }
                    />
                  </div>
                ) : !file ? (
                  <p className="p-6 text-sm text-muted-foreground">Select a file to compare.</p>
                ) : blockReason === "binary" ? (
                  <div className="p-6">
                    <EmptyState
                      icon={FileCode}
                      title="Binary file"
                      description="This path is not shown as text. Download it from Bitbucket if you need the bytes."
                    />
                  </div>
                ) : blockReason === "too_large" ? (
                  <div className="p-6">
                    <EmptyState
                      icon={FileCode}
                      title="File is too large to render"
                      description="The revision is locked, but the content exceeded the comparison size limit."
                    />
                  </div>
                ) : (
                  <CodeDiffViewer
                    key={`${file.path}:${(highlightAfterLines ?? []).join(",")}:${(highlightBeforeLines ?? []).join(",")}`}
                    path={file.path}
                    original={file.before.content ?? ""}
                    modified={file.after.content ?? ""}
                    sideBySide={sideBySide}
                    highlightBeforeLines={highlightBeforeLines}
                    highlightAfterLines={highlightAfterLines}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
