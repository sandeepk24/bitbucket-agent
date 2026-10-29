import { GitPullRequest } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";

export function PullRequests() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Pull Requests"
        description="Open, merged, and declined pull requests will appear here after Bitbucket ingestion is implemented."
      />
      <EmptyState
        icon={GitPullRequest}
        title="Pull request inbox is a placeholder"
        description="This page reserves routing for PR lists, reviewers, and merge status. Bitbucket integration is intentionally not implemented yet."
        milestone="Milestone 2"
      />
    </div>
  );
}
