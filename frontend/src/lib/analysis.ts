import type { AnalysisFinding, AnalysisSeverity, FindingKind } from "@/types/api";

export const SEVERITIES: AnalysisSeverity[] = ["critical", "high", "medium", "low", "info"];

export function filterFindings(
  findings: AnalysisFinding[],
  severity: AnalysisSeverity | "all",
  fileQuery: string
): AnalysisFinding[] {
  const needle = fileQuery.trim().toLowerCase();
  return findings.filter((finding) => {
    if (severity !== "all" && finding.severity !== severity) {
      return false;
    }
    if (!needle) {
      return true;
    }
    return (
      finding.path.toLowerCase().includes(needle) ||
      (finding.src_path ?? "").toLowerCase().includes(needle) ||
      finding.component.toLowerCase().includes(needle)
    );
  });
}

export function groupFindingsBySeverity(findings: AnalysisFinding[]): {
  severity: AnalysisSeverity;
  items: AnalysisFinding[];
}[] {
  return SEVERITIES.map((severity) => ({
    severity,
    items: findings.filter((finding) => finding.severity === severity),
  })).filter((group) => group.items.length > 0);
}

export function kindLabel(kind: FindingKind, source: string): string {
  if (kind === "confirmed") {
    return source === "static" ? "Confirmed · static analysis" : "Confirmed · model";
  }
  if (source === "model") {
    return "Hypothetical · model";
  }
  return "Hypothetical · runtime risk";
}

export function severityLabel(severity: AnalysisSeverity): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

export function countBySeverity(findings: AnalysisFinding[]): Record<AnalysisSeverity, number> {
  return SEVERITIES.reduce(
    (counts, severity) => {
      counts[severity] = findings.filter((finding) => finding.severity === severity).length;
      return counts;
    },
    {} as Record<AnalysisSeverity, number>
  );
}
