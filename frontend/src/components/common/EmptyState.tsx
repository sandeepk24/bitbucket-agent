import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "./Card";
import { Badge } from "./Badge";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  milestone?: string;
}

export function EmptyState({ icon: Icon, title, description, milestone }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center px-6 py-16 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        <p className="mt-2 max-w-lg text-sm text-muted-foreground">{description}</p>
        {milestone && (
          <Badge variant="outline" className="mt-4">
            {milestone}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}
