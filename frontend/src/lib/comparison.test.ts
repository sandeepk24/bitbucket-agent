import { describe, expect, it } from "vitest";
import {
  diffBlockReason,
  fileLabel,
  formatLineNumbers,
  languageFromPath,
  shortSha,
} from "./comparison";
import type { PullRequestFileComparison } from "@/types/api";

const sampleFile = (overrides: Partial<PullRequestFileComparison> = {}): PullRequestFileComparison => ({
  path: "backend/app/main.py",
  src_path: null,
  change_type: "MODIFY",
  base_sha: "0123456789abcdef0123456789abcdef01234567",
  head_sha: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  additions: 1,
  deletions: 1,
  before_lines: [12],
  after_lines: [14],
  truncated_diff: false,
  before: {
    path: "backend/app/main.py",
    revision: "0123456789abcdef0123456789abcdef01234567",
    content: "old",
    size: 3,
    binary: false,
    too_large: false,
    missing: false,
    truncated: false,
  },
  after: {
    path: "backend/app/main.py",
    revision: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    content: "new",
    size: 3,
    binary: false,
    too_large: false,
    missing: false,
    truncated: false,
  },
  ...overrides,
});

describe("languageFromPath", () => {
  it("maps common extensions for Monaco", () => {
    expect(languageFromPath("backend/app/client.py")).toBe("python");
    expect(languageFromPath("frontend/src/App.tsx")).toBe("typescript");
    expect(languageFromPath("Dockerfile")).toBe("dockerfile");
    expect(languageFromPath("notes.txt")).toBe("plaintext");
  });
});

describe("file comparison helpers", () => {
  it("labels renames and shortens SHAs", () => {
    expect(fileLabel({ path: "b.py", src_path: "a.py" })).toBe("a.py → b.py");
    expect(shortSha("a1b2c3d4e5f6a1b2")).toBe("a1b2c3d4e5f6");
  });

  it("blocks binary and oversized files", () => {
    expect(diffBlockReason(sampleFile())).toBe("ready");
    expect(
      diffBlockReason(
        sampleFile({
          after: { ...sampleFile().after, binary: true, content: null },
        })
      )
    ).toBe("binary");
    expect(
      diffBlockReason(
        sampleFile({
          before: { ...sampleFile().before, too_large: true, content: null },
        })
      )
    ).toBe("too_large");
  });

  it("formats changed line numbers", () => {
    expect(formatLineNumbers([])).toBe("—");
    expect(formatLineNumbers([12, 13])).toBe("12, 13");
  });
});
