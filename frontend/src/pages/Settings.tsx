import type { ReactNode } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { useSettings } from "@/api/queries";

export function Settings() {
  const { data, isLoading, error } = useSettings();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Non-secret runtime configuration. Tokens never leave the backend process."
      />
      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>Loaded from .env / process environment</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Spinner />
          ) : error ? (
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : "Could not load settings"}
            </p>
          ) : (
            <dl className="space-y-3 text-sm">
              <Row label="Application" value={data?.app_name} />
              <Row label="Version" value={data?.app_version} />
              <Row label="Bitbucket URL" value={data?.bitbucket_base_url} />
              <Row label="Workspace" value={data?.bitbucket_workspace || "not set"} />
              <Row
                label="Bitbucket token"
                value={
                  <Badge variant={data?.bitbucket_configured ? "success" : "outline"}>
                    {data?.bitbucket_configured ? "configured" : "not set"}
                  </Badge>
                }
              />
              <Row label="Bamboo URL" value={data?.bamboo_base_url || "not set"} />
              <Row
                label="Bamboo token"
                value={
                  <Badge variant={data?.bamboo_configured ? "success" : "outline"}>
                    {data?.bamboo_configured ? "configured" : "not set"}
                  </Badge>
                }
              />
              <Row label="AI provider" value={data?.ai_provider} />
              <Row label="AWS region" value={data?.aws_region} />
              <Row label="Bedrock model" value={data?.bedrock_model_id} />
              <Row
                label="Bedrock"
                value={
                  <Badge variant={data?.bedrock_configured ? "success" : "outline"}>
                    {data?.bedrock_configured ? "enabled" : "stub"}
                  </Badge>
                }
              />
              <Row
                label="Strands"
                value={
                  <Badge variant={data?.strands_configured ? "success" : "outline"}>
                    {data?.strands_configured ? "enabled" : "stub"}
                  </Badge>
                }
              />
            </dl>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border pb-3 last:border-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="break-all font-medium">{value || "—"}</dd>
    </div>
  );
}
