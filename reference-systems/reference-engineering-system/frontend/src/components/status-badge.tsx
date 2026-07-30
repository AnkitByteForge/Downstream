import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RFIStatus } from "@/lib/api-client";

const RFI_STATUS_STYLES: Record<RFIStatus, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  OPEN: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  RESPONDED: "bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-300",
  CLOSED: "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-300",
};

export function RFIStatusBadge({ status }: { status: RFIStatus }) {
  return (
    <Badge variant="outline" className={cn("border-transparent font-medium", RFI_STATUS_STYLES[status])}>
      {status}
    </Badge>
  );
}

export function BallInCourtBadge({ ballInCourt }: { ballInCourt: string }) {
  return (
    <Badge variant="secondary" className="font-normal capitalize">
      {ballInCourt}
    </Badge>
  );
}

const DRAWING_VERSION_STATUS_STYLES: Record<string, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  ISSUED: "bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-300",
  REVISED: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  SUPERSEDED: "bg-muted text-muted-foreground line-through decoration-1",
};

export function DrawingVersionStatusBadge({ status }: { status: string }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        DRAWING_VERSION_STATUS_STYLES[status] ?? "bg-muted"
      )}
    >
      {status}
    </Badge>
  );
}
