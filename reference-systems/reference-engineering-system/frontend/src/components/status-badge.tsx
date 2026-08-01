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

/** Color is driven entirely by gates_procurement, never by matching a
 * specific status code — the vocabulary is configuration-driven (ADR-003),
 * so the UI can't hardcode per-code styling either. */
export function SubmittalStatusBadge({
  label,
  gatesProcurement,
}: {
  label: string;
  gatesProcurement: boolean;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "border-transparent font-medium",
        gatesProcurement
          ? "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-300"
          : "bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-300"
      )}
    >
      {label}
    </Badge>
  );
}

export function LongLeadBadge() {
  return (
    <Badge
      variant="outline"
      className="border-transparent bg-amber-100 text-amber-900 font-medium dark:bg-amber-950 dark:text-amber-300"
    >
      Long lead
    </Badge>
  );
}
