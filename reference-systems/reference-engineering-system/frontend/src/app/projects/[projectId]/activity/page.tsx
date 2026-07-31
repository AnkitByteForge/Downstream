"use client";

import { use, useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRequireSession } from "@/lib/auth/use-session";
import { activityApi, type ActivityEntryOut } from "@/lib/api-client";

function describe(entry: ActivityEntryOut): string {
  return `${entry.resource_name.slice(0, -1)} #${entry.resource_id} — ${entry.event_type}`;
}

export default function ActivityFeedPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [entries, setEntries] = useState<ActivityEntryOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    activityApi.list(Number(projectId)).then(setEntries);
  }, [session, projectId]);

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Activity Feed"
        description="Every outbound webhook this system has attempted to dispatch, most recent first."
      />
      <div className="p-6">
        {entries === null ? (
          <Skeleton className="h-64 w-full" />
        ) : entries.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              No activity yet — closing an RFI with a registered webhook subscription will appear
              here.
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col gap-2">
            {entries.map((entry) => (
              <Card key={entry.id}>
                <CardContent className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    {entry.status === "SENT" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-destructive" />
                    )}
                    <div>
                      <div className="text-sm font-medium">{describe(entry)}</div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(entry.dispatched_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <span className="text-xs font-medium uppercase text-muted-foreground">
                    {entry.status}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
