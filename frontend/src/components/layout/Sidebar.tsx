import { NavLink } from "react-router-dom";
import { ChevronsLeft, ChevronsRight, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { navSections } from "@/lib/nav";
import { StatusIndicator } from "@/components/common/StatusIndicator";
import { Button } from "@/components/common/Button";
import { useHealth } from "@/api/queries";

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onClose: () => void;
  onToggleCollapse: () => void;
}

export function Sidebar({ collapsed, mobileOpen, onClose, onToggleCollapse }: SidebarProps) {
  const { data: health, isLoading } = useHealth();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex h-screen flex-col border-r border-border bg-sidebar transition-all duration-200 lg:static",
        collapsed ? "w-[4.5rem]" : "w-64",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}
    >
      <div
        className={cn(
          "flex h-16 items-center border-b border-border",
          collapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary">
            <svg viewBox="0 0 32 32" className="h-5 w-5" aria-hidden="true">
              <path
                d="M7 11.5h18l-2.2 9.4c-.3 1.3-1.4 2.2-2.7 2.2H11.9c-1.3 0-2.4-.9-2.7-2.2L7 11.5z"
                fill="white"
              />
            </svg>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">Bitbucket Agent</p>
              <p className="truncate text-[11px] text-muted-foreground">DevOps Intelligence</p>
            </div>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onClose}
          aria-label="Close navigation"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {navSections.map((section) => (
          <div key={section.title}>
            {!collapsed && (
              <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {section.title}
              </p>
            )}
            <div className="space-y-1">
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  title={collapsed ? label : undefined}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center rounded-md text-sm font-medium transition-colors",
                      collapsed ? "justify-center px-0 py-2.5" : "gap-3 px-3 py-2.5",
                      isActive
                        ? "bg-accent text-sidebar-active"
                        : "text-sidebar-foreground hover:bg-accent/50 hover:text-sidebar-active"
                    )
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span className="truncate">{label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="space-y-2 border-t border-border px-3 py-3">
        {!collapsed && (
          <>
            <StatusIndicator
              status={health ? "connected" : isLoading ? "loading" : "disconnected"}
              label="Backend"
              detail={health?.version}
            />
            <StatusIndicator
              status={
                isLoading ? "loading" : health?.bitbucket_configured ? "connected" : "disconnected"
              }
              label="Bitbucket"
              detail={health?.bitbucket_configured ? "token set" : "not configured"}
            />
            <StatusIndicator
              status={
                isLoading ? "loading" : health?.bamboo_configured ? "connected" : "disconnected"
              }
              label="Bamboo"
              detail={health?.bamboo_configured ? "token set" : "not configured"}
            />
            <StatusIndicator
              status={
                isLoading
                  ? "loading"
                  : health?.bedrock_configured || health?.strands_configured
                    ? "connected"
                    : "disconnected"
              }
              label="AI"
              detail={health?.ai_provider ?? "stub"}
            />
          </>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="hidden w-full lg:inline-flex"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}
