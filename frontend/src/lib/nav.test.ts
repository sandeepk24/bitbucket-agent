import { describe, expect, it } from "vitest";
import { allNavItems, navItemForPath, navSections } from "./nav";

describe("navigation", () => {
  it("exposes the seven workspace destinations", () => {
    const labels = allNavItems.map((item) => item.label);
    expect(labels).toEqual([
      "Dashboard",
      "Repositories",
      "Pull Requests",
      "PR Deep Analysis",
      "Bamboo Builds",
      "Production Investigation",
      "Settings",
    ]);
  });

  it("groups items into overview, workspace, operations, and system", () => {
    expect(navSections.map((section) => section.title)).toEqual([
      "Overview",
      "Workspace",
      "Operations",
      "System",
    ]);
  });

  it("resolves breadcrumbs from the current path", () => {
    expect(navItemForPath("/pr-analysis").label).toBe("PR Deep Analysis");
    expect(navItemForPath("/pull-requests/DEV/payments/42").label).toBe("Pull Requests");
    expect(navItemForPath("/").label).toBe("Dashboard");
  });
});
