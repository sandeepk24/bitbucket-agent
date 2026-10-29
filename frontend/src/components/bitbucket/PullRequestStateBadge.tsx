import { Badge } from "@/components/common/Badge";

export function PullRequestStateBadge({ state }: { state: string }) {
  const variant =
    state === "OPEN" ? "success" : state === "DECLINED" ? "destructive" : state === "MERGED" ? "default" : "outline";
  return <Badge variant={variant}>{state.toLowerCase()}</Badge>;
}
