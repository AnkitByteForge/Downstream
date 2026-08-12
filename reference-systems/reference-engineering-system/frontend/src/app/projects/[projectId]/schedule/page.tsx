"use client";

import { use, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRequireSession } from "@/lib/auth/use-session";
import { scheduleActivitiesApi, type ScheduleActivityOut } from "@/lib/api-client";

export default function ScheduleRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [activities, setActivities] = useState<ScheduleActivityOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    void scheduleActivitiesApi.list(Number(projectId)).then(setActivities);
  }, [session, projectId]);

  const activityById = new Map((activities ?? []).map((a) => [a.id, a]));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Schedule"
        description="Primavera-shaped schedule activities — procurement chains, predecessor/successor links, and submittal scheduling."
      />
      <div className="p-6">
        {activities === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Activity code</TableHead>
                  <TableHead className="w-32">Type</TableHead>
                  <TableHead className="w-28">WBS</TableHead>
                  <TableHead>Predecessors</TableHead>
                  <TableHead>Successors</TableHead>
                  <TableHead>Linked submittals</TableHead>
                  <TableHead className="w-44">Delivery milestone</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activities.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                      No schedule activities on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {activities.map((activity) => (
                  <TableRow key={activity.id}>
                    <TableCell className="font-medium">{activity.activity_code}</TableCell>
                    <TableCell className="capitalize">{activity.type.toLowerCase()}</TableCell>
                    <TableCell>{activity.wbs ?? "—"}</TableCell>
                    <TableCell>
                      {activity.predecessor_ids.length === 0
                        ? "—"
                        : activity.predecessor_ids
                            .map((id) => activityById.get(id)?.activity_code ?? `#${id}`)
                            .join(", ")}
                    </TableCell>
                    <TableCell>
                      {activity.successor_ids.length === 0
                        ? "—"
                        : activity.successor_ids
                            .map((id) => activityById.get(id)?.activity_code ?? `#${id}`)
                            .join(", ")}
                    </TableCell>
                    <TableCell>
                      {activity.linked_submittal_ids.length === 0
                        ? "—"
                        : activity.linked_submittal_ids.length}
                    </TableCell>
                    <TableCell>
                      {activity.delivery_milestone
                        ? new Date(activity.delivery_milestone).toLocaleDateString()
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
