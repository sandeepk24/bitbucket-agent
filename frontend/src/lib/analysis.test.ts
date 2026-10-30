import { describe, expect, it } from "vitest";
import { filterFindings, groupFindingsBySeverity, kindLabel } from "./analysis";
import type { AnalysisFinding } from "@/types/api";

function finding(overrides: Partial<AnalysisFinding> = {}): AnalysisFinding {
  return {
    id: "1",
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
    evidence: [],
    risk: "secret in git",
    recommended_fix: "use a secret manager",
    production_impact: "credential leak",
    ...overrides,
  };
}

describe("filterFindings", () => {
  const items = [
    finding(),
    finding({
      id: "2",
      title: "Renamed module",
      severity: "medium",
      kind: "hypothetical",
      source: "heuristic",
      path: "backend/app/util/display.py",
      src_path: "backend/app/util/names.py",
    }),
  ];

  it("filters by severity and file name", () => {
    expect(filterFindings(items, "all", "").length).toBe(2);
    expect(filterFindings(items, "critical", "").map((item) => item.id)).toEqual(["1"]);
    expect(filterFindings(items, "all", "display.py").map((item) => item.id)).toEqual(["2"]);
    expect(filterFindings(items, "all", "names.py").map((item) => item.id)).toEqual(["2"]);
  });
});

describe("groupFindingsBySeverity", () => {
  it("keeps severity order and drops empty groups", () => {
    const groups = groupFindingsBySeverity([
      finding({ severity: "low", id: "l" }),
      finding({ severity: "critical", id: "c" }),
    ]);
    expect(groups.map((group) => group.severity)).toEqual(["critical", "low"]);
  });
});

describe("kindLabel", () => {
  it("distinguishes confirmed static findings from hypothetical runtime risks", () => {
    expect(kindLabel("confirmed", "static")).toBe("Confirmed · static analysis");
    expect(kindLabel("hypothetical", "heuristic")).toBe("Hypothetical · runtime risk");
    expect(kindLabel("hypothetical", "model")).toBe("Hypothetical · model");
  });
});
