import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { Spinner } from "@/components/common/Spinner";
import { useHealth, useSettings } from "@/api/queries";
import { allNavItems } from "@/lib/nav";

export function Dashboard() {
  const { data: health, isLoading, error } = useHealth();
  const { data: settings } = useSettings();

  const modules = allNavItems.filter((item) => item.to !== "/");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Foundation health for Bitbucket, Bamboo, and AI-assisted investigation. Integrations are not wired yet."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          title="API"
          loading={isLoading}
          ok={Boolean(health)}
          detail={
            health
              ? `v${health.version}`
              : error instanceof Error
                ? error.message
                : "checking"
          }
        />
        <StatusCard
          title="Bitbucket"
          loading={isLoading}
          ok={Boolean(health?.bitbucket_configured)}
          detail={health?.bitbucket_configured ? "token present" : "set BITBUCKET_TOKEN later"}
        />
        <StatusCard
          title="Bamboo"
          loading={isLoading}
          ok={Boolean(health?.bamboo_configured)}
          detail={health?.bamboo_configured ? "token present" : "set BAMBOO_TOKEN later"}
        />
        <StatusCard
          title="AI providers"
          loading={isLoading}
          ok={Boolean(health?.bedrock_configured || health?.strands_configured)}
          detail={`${health?.ai_provider ?? "bedrock"} stub`}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Workspace modules</CardTitle>
            <CardDescription>
              Navigation and routing are in place. Data sources land in later milestones.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {modules.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="rounded-lg border border-border bg-secondary/40 p-4 transition-colors hover:border-primary/40 hover:bg-secondary"
              >
                <div className="flex items-center gap-2">
                  <item.icon className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium text-foreground">{item.label}</p>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">{item.description}</p>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Runtime</CardTitle>
            <CardDescription>Loaded from environment, secrets omitted</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>Bitbucket host: {settings?.bitbucket_base_url ?? "—"}</p>
            <p>Workspace: {settings?.bitbucket_workspace || "not set"}</p>
            <p>Bamboo host: {settings?.bamboo_base_url || "not set"}</p>
            <p>AWS region: {settings?.aws_region ?? "—"}</p>
            <p>Bedrock model: {settings?.bedrock_model_id ?? "—"}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusCard({
  title,
  loading,
  ok,
  detail,
}: {
  title: string;
  loading: boolean;
  ok: boolean;
  detail: string;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        {loading ? (
          <Spinner className="mt-3" />
        ) : (
          <>
            <div className="mt-2">
              <Badge variant={ok ? "success" : "outline"}>{ok ? "ready" : "not configured"}</Badge>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">{detail}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
