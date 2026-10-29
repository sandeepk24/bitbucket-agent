import { ScanSearch } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";

export function PrDeepAnalysis() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="PR Deep Analysis"
        description="AI-assisted review of diffs, risk, and test coverage using Amazon Bedrock or Strands Agents."
      />
      <EmptyState
        icon={ScanSearch}
        title="Deep analysis is not available yet"
        description="Later milestones will send pull request context to Bedrock or Strands. Provider interfaces exist, but no model inference runs in this foundation."
        milestone="Milestone 3"
      />
    </div>
  );
}
