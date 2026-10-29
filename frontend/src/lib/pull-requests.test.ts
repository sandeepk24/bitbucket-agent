import { describe, expect, it } from "vitest";
import { matchesPullRequest } from "./pull-requests";
import type { BitbucketPullRequest } from "@/types/api";

const sample: BitbucketPullRequest = {
  id: 42,
  version: 1,
  title: "Harden token handling in the payments API",
  description: null,
  state: "OPEN",
  open: true,
  closed: false,
  created_date: 1711900800000,
  updated_date: 1711987200000,
  html_url: null,
  author: {
    name: "tom",
    display_name: "Tom Rivera",
    email: "tom@example.com",
    slug: "tom",
  },
  reviewers: [
    {
      user: { name: "jcitizen", display_name: "Jane Citizen", email: null, slug: "jcitizen" },
      role: "REVIEWER",
      approved: true,
      status: "APPROVED",
    },
  ],
  source_branch: "feature/token-redaction",
  destination_branch: "main",
  source_commit: null,
  destination_commit: null,
  approved_count: 1,
  reviewer_count: 1,
};

describe("matchesPullRequest", () => {
  it("matches id, title, author, and branches", () => {
    expect(matchesPullRequest(sample, "")).toBe(true);
    expect(matchesPullRequest(sample, "42")).toBe(true);
    expect(matchesPullRequest(sample, "token")).toBe(true);
    expect(matchesPullRequest(sample, "tom rivera")).toBe(true);
    expect(matchesPullRequest(sample, "feature/token")).toBe(true);
    expect(matchesPullRequest(sample, "jane")).toBe(true);
    expect(matchesPullRequest(sample, "no-such-pr")).toBe(false);
  });
});
