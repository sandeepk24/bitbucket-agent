import { Check, CircleAlert, CircleDashed, LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnalysisStage } from "@/types/api";

const PENDING_STAGES: AnalysisStage[] = [
  { id: "resolve-pr", label: "Load pull request metadata", status: "running", detail: null },
  { id: "resolve-revisions", label: "Lock base and head SHAs", status: "pending", detail: null },
  { id: "load-changes", label: "List changed files", status: "pending", detail: null },
  { id: "static-review", label: "Run confirmed static analysis", status: "pending", detail: null },
  { id: "model-inference", label: "AI model review", status: "pending", detail: null },
  { id: "assemble", label: "Assemble report", status: "pending", detail: null },
];

interface AnalysisProgressProps {
  stages?: AnalysisStage[];
  pending?: boolean;
}

export function AnalysisProgress({ stages, pending = false }: AnalysisProgressProps) {
  const items = stages?.length ? stages : pending ? PENDING_STAGES : [];
  if (items.length === 0) {
    return null;
  }

  return (
    <ol className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
      {items.map((stage) => (
        <li
          key={stage.id}
          className="flex items-start gap-3 rounded-md border border-border bg-secondary/40 px-3 py-2"
        >
          <StageIcon status={pending && !stages?.length && stage.status === "running" ? "running" : stage.status} />
          <div className="min-w-0">
            <p className="text-sm font-medium">{stage.label}</p>
            {stage.detail && <p className="truncate text-xs text-muted-foreground">{stage.detail}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

function StageIcon({ status }: { status: AnalysisStage["status"] }) {
  const className = "mt-0.5 h-4 w-4 shrink-0";
  if (status === "done") {
    return <Check className={cn(className, "text-success")} />;
  }
  if (status === "error") {
    return <CircleAlert className={cn(className, "text-destructive")} />;
  }
  if (status === "running") {
    return <LoaderCircle className={cn(className, "animate-spin text-primary")} />;
  }
  return <CircleDashed className={cn(className, "text-muted-foreground")} />;
}
