import type { ComparisonFileSummary, PullRequestFileComparison } from "@/types/api";

const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  py: "python",
  ts: "typescript",
  tsx: "typescript",
  js: "javascript",
  jsx: "javascript",
  json: "json",
  md: "markdown",
  yml: "yaml",
  yaml: "yaml",
  java: "java",
  go: "go",
  rs: "rust",
  xml: "xml",
  html: "html",
  css: "css",
  scss: "scss",
  sh: "shell",
  bash: "shell",
  sql: "sql",
  kt: "kotlin",
  swift: "swift",
  rb: "ruby",
  php: "php",
  c: "c",
  h: "c",
  cpp: "cpp",
  cc: "cpp",
  cs: "csharp",
  toml: "ini",
  ini: "ini",
  properties: "ini",
  gradle: "java",
};

export function languageFromPath(path: string): string {
  const name = path.split("/").pop()?.toLowerCase() ?? "";
  if (name === "dockerfile") {
    return "dockerfile";
  }
  const ext = name.includes(".") ? name.slice(name.lastIndexOf(".") + 1) : "";
  return LANGUAGE_BY_EXTENSION[ext] ?? "plaintext";
}

export function fileLabel(file: Pick<ComparisonFileSummary, "path" | "src_path">): string {
  return file.src_path ? `${file.src_path} → ${file.path}` : file.path;
}

export function shortSha(sha: string | null | undefined): string {
  if (!sha) {
    return "—";
  }
  return sha.slice(0, 12);
}

export type DiffBlockReason = "ready" | "binary" | "too_large";

export function diffBlockReason(file: PullRequestFileComparison): DiffBlockReason {
  if (file.before.binary || file.after.binary) {
    return "binary";
  }
  if (file.before.too_large || file.after.too_large) {
    return "too_large";
  }
  return "ready";
}

export function formatLineNumbers(lines: number[]): string {
  if (lines.length === 0) {
    return "—";
  }
  const unique = [...new Set(lines)];
  if (unique.length <= 8) {
    return unique.join(", ");
  }
  return `${unique.slice(0, 8).join(", ")}…`;
}
