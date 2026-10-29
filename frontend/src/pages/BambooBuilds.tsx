import { Hammer } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";

export function BambooBuilds() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Bamboo Builds"
        description="Build plans, results, and failure clustering will land here after the Bamboo client is implemented."
      />
      <EmptyState
        icon={Hammer}
        title="Bamboo is not connected yet"
        description="This page is a placeholder so operations navigation is in place before build ingestion. No Bamboo HTTP calls are made in this milestone."
        milestone="Milestone 3"
      />
    </div>
  );
}
