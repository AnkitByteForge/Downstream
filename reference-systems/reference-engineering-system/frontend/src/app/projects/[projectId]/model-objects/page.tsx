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
import {
  locationsApi,
  modelObjectsApi,
  scheduleActivitiesApi,
  type LocationOut,
  type ModelObjectOut,
  type ScheduleActivityOut,
} from "@/lib/api-client";

export default function ModelObjectsRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [objects, setObjects] = useState<ModelObjectOut[] | null>(null);
  const [locations, setLocations] = useState<LocationOut[]>([]);
  const [activities, setActivities] = useState<ScheduleActivityOut[]>([]);

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);
    async function load() {
      const [objectList, locs, activityList] = await Promise.all([
        modelObjectsApi.list(pid),
        locationsApi.list(pid),
        scheduleActivitiesApi.list(pid),
      ]);
      setObjects(objectList);
      setLocations(locs);
      setActivities(activityList);
    }
    void load();
  }, [session, projectId]);

  const locationLookup = new Map(locations.map((l) => [l.id, l]));
  const activityLookup = new Map(activities.map((a) => [a.id, a]));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Model Objects"
        description="BIM/3D coordination objects — discipline, location, appearance profile, and their SYNCHRO-style schedule resource link."
      />
      <div className="p-6">
        {objects === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Discipline</TableHead>
                  <TableHead className="w-36">Appearance profile</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Resource link (schedule activity)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {objects.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center text-muted-foreground">
                      No model objects on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {objects.map((obj) => (
                  <TableRow key={obj.id}>
                    <TableCell className="font-medium">{obj.discipline_code}</TableCell>
                    <TableCell className="capitalize">
                      {obj.appearance_profile.toLowerCase()}
                    </TableCell>
                    <TableCell>
                      {obj.location_id != null
                        ? locationLookup.get(obj.location_id)?.name ?? `#${obj.location_id}`
                        : "—"}
                    </TableCell>
                    <TableCell>
                      {obj.resource_link_id != null
                        ? activityLookup.get(obj.resource_link_id)?.activity_code ??
                          `#${obj.resource_link_id}`
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
