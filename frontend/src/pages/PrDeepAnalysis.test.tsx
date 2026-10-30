import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { PrDeepAnalysis } from "./PrDeepAnalysis";
import type { PullRequestAnalysis } from "@/types/api";

vi.mock("@monaco-editor/react", () => ({
  DiffEditor: () => <div data-testid="monaco-diff" />,
  loader: { config: vi.fn() },
}));
vi.mock("@/lib/monaco", () => ({}));

const analysis: PullRequestAnalysis = {
  status: "partial",
  project_key: "DEV",
  repo_slug: "payments",
  pull_request_id: 42,
  title: "Harden token handling",
  source_branch: "feature/token-redaction",
  destination_branch: "main",
  base_sha: "0123456789abcdef0123456789abcdef01234567",
  head_sha: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  commit_count: 2,
  summary: "Static review found a hardcoded password.",
  production_impact: "Treat confirmed high findings as merge blockers.",
  risk_summary: "Highest finding: critical — Hardcoded credential in source.",
  progress: [
    { id: "static-review", label: "Run confirmed static analysis", status: "done", detail: "4 text files" },
    { id: "model-inference", label: "AI model review", status: "skipped", detail: "AI provider is not configured" },
  ],
  model: { provider: "bedrock", available: false, used: false, error: "AI provider is not configured" },
  components: [{ name: "backend/app", file_count: 4, finding_count: 2, paths: ["backend/app/api/login.py"] }],
  files: [],
  unsupported_files: [
    { path: "frontend/public/logo.png", reason: "binary", detail: "Binary files are not sent to static review or the model." },
  ],
  findings: [
    {
      id: "static-secret",
      title: "Hardcoded credential in source",
      severity: "critical",
      kind: "confirmed",
      source: "static",
      path: "backend/app/api/login.py",
      src_path: null,
      change_type: "ADD",
      component: "backend/app",
      before_lines: [],
      after_lines: [1],
      evidence: [
        {
          path: "backend/app/api/login.py",
          revision: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
          line: 1,
          quote: 'password = "hunter2"',
        },
      ],
      risk: "A secret appears as a literal.",
      recommended_fix: "Move the value to a secret store.",
      production_impact: "A leaked credential can be used against production.",
    },
    {
      id: "heuristic-auth",
      title: "Security-sensitive path removed",
      severity: "high",
      kind: "hypothetical",
      source: "heuristic",
      path: "backend/app/legacy/auth.py",
      src_path: null,
      change_type: "DELETE",
      component: "backend/app",
      before_lines: [1],
      after_lines: [],
      evidence: [],
      risk: "Removing auth code can drop checks.",
      recommended_fix: "Confirm callers still authenticate.",
      production_impact: "Unauthenticated access if this module was wired.",
    },
  ],
};

vi.mock("@/api/queries", () => ({
  useBitbucketHealth: () => ({ data: { configured: true, reachable: true, authenticated: true }, isLoading: false }),
  useBitbucketPullRequests: () => ({
    data: {
      items: [{ id: 42, title: "Harden token handling" }],
    },
    isLoading: false,
  }),
  usePullRequestAnalysis: () => ({
    data: analysis,
    isLoading: false,
    isFetching: false,
    error: null,
  }),
  useBitbucketProjects: () => ({ data: { items: [{ key: "DEV", name: "Dev" }] }, isLoading: false, error: null }),
  useBitbucketRepos: () => ({ data: { items: [{ slug: "payments", name: "payments" }] }, isLoading: false, error: null }),
  useBitbucketPullRequestComparison: () => ({ data: { files: [], base: { sha: "a" }, head: { sha: "b" } }, isLoading: false, error: null }),
  useBitbucketPullRequestFileComparison: () => ({ data: null, isLoading: false, error: null }),
}));

describe("PrDeepAnalysis", () => {
  it("shows summary, grouped findings, model error, and unsupported files", () => {
    render(
      <MemoryRouter initialEntries={["/pr-analysis?project=DEV&repo=payments&pr=42"]}>
        <PrDeepAnalysis />
      </MemoryRouter>
    );

    expect(screen.getByText("Static review found a hardcoded password.")).toBeInTheDocument();
    expect(screen.getAllByText("Hardcoded credential in source").length).toBeGreaterThan(0);
    expect(screen.getByText(/Model error: AI provider is not configured/)).toBeInTheDocument();
    expect(screen.getByText(/frontend\/public\/logo.png/)).toBeInTheDocument();
    expect(screen.getAllByText("Confirmed · static analysis").length).toBeGreaterThan(0);
  });

  it("filters findings by severity and jumps to the selected file", () => {
    render(
      <MemoryRouter initialEntries={["/pr-analysis?project=DEV&repo=payments&pr=42"]}>
        <PrDeepAnalysis />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Filter High" }));
    expect(screen.queryByText("Hardcoded credential in source")).not.toBeInTheDocument();
    expect(screen.getAllByText("Security-sensitive path removed").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /Security-sensitive path removed/i }));
    expect(screen.getAllByText("Hypothetical · runtime risk").length).toBeGreaterThan(0);
  });
});
