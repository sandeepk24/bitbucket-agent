import { useLocation } from "react-router-dom";
import { Bell, Menu, Search } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Badge } from "@/components/common/Badge";
import { useHealth } from "@/api/queries";
import { navItemForPath } from "@/lib/nav";
import { cn } from "@/lib/utils";

interface TopNavProps {
  onMenuClick: () => void;
}

export function TopNav({ onMenuClick }: TopNavProps) {
  const location = useLocation();
  const current = navItemForPath(location.pathname);
  const { data: health, isLoading } = useHealth();

  const apiStatus = health ? "connected" : isLoading ? "checking" : "offline";

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-3 border-b border-border bg-topnav/95 px-4 backdrop-blur lg:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <nav aria-label="Breadcrumb" className="hidden min-w-0 items-center gap-2 text-sm sm:flex">
        <span className="text-muted-foreground">Bitbucket Agent</span>
        <span className="text-muted-foreground">/</span>
        <span className="truncate font-medium text-foreground">{current.label}</span>
      </nav>

      <div className="mx-auto hidden w-full max-w-md md:block">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            disabled
            placeholder="Search repositories, PRs, builds (coming later)"
            className="h-9 w-full rounded-md border border-border bg-background/60 pl-9 pr-3 text-sm text-muted-foreground outline-none"
          />
        </label>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Badge variant="outline">Foundation</Badge>
        <span
          className={cn(
            "hidden items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs sm:inline-flex",
            apiStatus === "connected" && "text-success",
            apiStatus === "checking" && "text-warning",
            apiStatus === "offline" && "text-destructive"
          )}
        >
          <span
            className={cn("h-1.5 w-1.5 rounded-full", {
              "bg-success": apiStatus === "connected",
              "bg-warning": apiStatus === "checking",
              "bg-destructive": apiStatus === "offline",
            })}
          />
          API {apiStatus}
        </span>
        <Button variant="ghost" size="icon" disabled aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary"
          title="Local operator"
        >
          BA
        </div>
      </div>
    </header>
  );
}
