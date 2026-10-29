import { ShieldAlert } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";

export function ProductionInvestigation() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Production Investigation"
        description="Correlate pull requests, Bamboo builds, and production signals when an incident needs a timeline."
      />
      <EmptyState
        icon={ShieldAlert}
        title="Investigation workspace is reserved"
        description="This surface will stitch repository activity, CI failures, and runtime clues. Data sources are not connected in the foundation milestone."
        milestone="Milestone 4"
      />
    </div>
  );
}
