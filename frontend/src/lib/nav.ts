import {
  LayoutDashboard,
  GitBranch,
  GitPullRequest,
  ScanSearch,
  Hammer,
  ShieldAlert,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  description: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const navSections: NavSection[] = [
  {
    title: "Overview",
    items: [
      {
        to: "/",
        label: "Dashboard",
        icon: LayoutDashboard,
        description: "Platform health and foundation status",
      },
    ],
  },
  {
    title: "Workspace",
    items: [
      {
        to: "/repositories",
        label: "Repositories",
        icon: GitBranch,
        description: "Bitbucket repositories in the connected workspace",
      },
      {
        to: "/pull-requests",
        label: "Pull Requests",
        icon: GitPullRequest,
        description: "Open and recently merged pull requests",
      },
      {
        to: "/pr-analysis",
        label: "PR Deep Analysis",
        icon: ScanSearch,
        description: "AI-assisted review of diffs, risk, and test coverage",
      },
    ],
  },
  {
    title: "Operations",
    items: [
      {
        to: "/bamboo",
        label: "Bamboo Builds",
        icon: Hammer,
        description: "Build plans, results, and failure clustering",
      },
      {
        to: "/production",
        label: "Production Investigation",
        icon: ShieldAlert,
        description: "Correlate PRs, builds, and production signals",
      },
    ],
  },
  {
    title: "System",
    items: [
      {
        to: "/settings",
        label: "Settings",
        icon: Settings,
        description: "Non-secret runtime configuration",
      },
    ],
  },
];

export const allNavItems: NavItem[] = navSections.flatMap((section) => section.items);

export function navItemForPath(pathname: string): NavItem {
  const match = allNavItems.find((item) =>
    item.to === "/" ? pathname === "/" : pathname.startsWith(item.to)
  );
  return match ?? allNavItems[0];
}
