import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PullRequestComparison } from "./PullRequestComparison";
import type { PullRequestComparison as Comparison, PullRequestFileComparison } from "@/types/api";

vi.mock("@monaco-editor/react", () => ({
  DiffEditor: ({
    original,
    modified,
    options,
  }: {
    original: string;
    modified: string;
    options?: { renderSideBySide?: boolean };
  }) => (
    <div data-testid="monaco-diff" data-side-by-side={String(options?.renderSideBySide)}>
      <pre data-testid="diff-before">{original}</pre>
      <pre data-testid="diff-after">{modified}</pre>
    </div>
  ),
  loader: { config: vi.fn() },
}));

vi.mock("@/lib/monaco", () => ({}));

const comparison: Comparison = {
  project_key: "DEV",
  repo_slug: "payments",
  pull_request_id: 42,
  base: { sha: "0123456789abcdef0123456789abcdef01234567", display_id: "0123456", role: "base" },
  head: { sha: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", display_id: "a1b2c3d", role: "head" },
  target: { sha: "cafebabecafebabecafebabecafebabecafebabe", display_id: "cafebab", role: "target" },
  commit_count: 2,
  truncated_diff: false,
  files: [
    {
      path: "backend/app/providers/bitbucket/client.py",
      src_path: null,
      change_type: "MODIFY",
      additions: 1,
      deletions: 1,
      before_lines: [12],
      after_lines: [12],
      binary: false,
      truncated_diff: false,
      hunks_available: true,
    },
    {
      path: "backend/app/core/secrets.py",
      src_path: null,
      change_type: "ADD",
      additions: 1,
      deletions: 0,
      before_lines: [],
      after_lines: [1],
      binary: false,
      truncated_diff: false,
      hunks_available: true,
    },
  ],
};

const modifiedFile: PullRequestFileComparison = {
  path: "backend/app/providers/bitbucket/client.py",
  src_path: null,
  change_type: "MODIFY",
  base_sha: comparison.base.sha,
  head_sha: comparison.head.sha,
  additions: 1,
  deletions: 1,
  before_lines: [12],
  after_lines: [12],
  truncated_diff: false,
  before: {
    path: "backend/app/providers/bitbucket/client.py",
    revision: comparison.base.sha,
    content: "old client",
    size: 10,
    binary: false,
    too_large: false,
    missing: false,
    truncated: false,
  },
  after: {
    path: "backend/app/providers/bitbucket/client.py",
    revision: comparison.head.sha,
    content: "new client",
    size: 10,
    binary: false,
    too_large: false,
    missing: false,
    truncated: false,
  },
};

const addedFile: PullRequestFileComparison = {
  ...modifiedFile,
  path: "backend/app/core/secrets.py",
  change_type: "ADD",
  before_lines: [],
  after_lines: [1],
  before: {
    ...modifiedFile.before,
    path: "backend/app/core/secrets.py",
    content: "",
    missing: true,
  },
  after: {
    ...modifiedFile.after,
    path: "backend/app/core/secrets.py",
    content: "def redact():",
  },
};

vi.mock("@/api/queries", () => ({
  useBitbucketPullRequestComparison: () => ({
    data: comparison,
    isLoading: false,
    error: null,
  }),
  useBitbucketPullRequestFileComparison: (
    _project: string | undefined,
    _repo: string | undefined,
    _id: string | undefined,
    file: { path: string } | null
  ) => ({
    data: file?.path.endsWith("secrets.py") ? addedFile : modifiedFile,
    isLoading: false,
    error: null,
  }),
}));

describe("PullRequestComparison", () => {
  it("renders a split diff for the selected file and can switch to inline", () => {
    render(<PullRequestComparison projectKey="DEV" repoSlug="payments" pullRequestId="42" />);

    expect(screen.getByText(/Locked to 0123456789ab/)).toBeInTheDocument();
    expect(screen.getByTestId("diff-before")).toHaveTextContent("old client");
    expect(screen.getByTestId("diff-after")).toHaveTextContent("new client");
    expect(screen.getByTestId("monaco-diff")).toHaveAttribute("data-side-by-side", "true");

    fireEvent.click(screen.getByRole("button", { name: /inline/i }));
    expect(screen.getByTestId("monaco-diff")).toHaveAttribute("data-side-by-side", "false");
  });

  it("navigates between changed files", () => {
    render(<PullRequestComparison projectKey="DEV" repoSlug="payments" pullRequestId="42" />);

    fireEvent.click(screen.getByRole("button", { name: /secrets\.py/i }));
    expect(screen.getByTestId("diff-after")).toHaveTextContent("def redact():");
  });
});
