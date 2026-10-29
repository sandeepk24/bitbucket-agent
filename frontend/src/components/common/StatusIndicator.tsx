import { cn } from "@/lib/utils";

interface StatusIndicatorProps {
  status: "connected" | "disconnected" | "loading";
  label: string;
  detail?: string;
}

export function StatusIndicator({ status, label, detail }: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn("h-2 w-2 shrink-0 rounded-full", {
          "animate-pulse bg-success": status === "connected",
          "bg-destructive": status === "disconnected",
          "animate-pulse bg-warning": status === "loading",
        })}
      />
      <span className="truncate text-xs text-foreground">{label}</span>
      {detail && (
        <span className="truncate text-[11px] text-muted-foreground">({detail})</span>
      )}
    </div>
  );
}
