import { GitBranch } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";

export function Repositories() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Repositories"
        description="Browse Bitbucket repositories in the connected workspace once the API client is wired."
      />
      <EmptyState
        icon={GitBranch}
        title="Repository browser is not connected yet"
        description="Milestone 2 will list repositories, default branches, and clone URLs from Bitbucket Cloud or Data Center. No REST calls are made in this foundation."
        milestone="Milestone 2"
      />
    </div>
  );
}
