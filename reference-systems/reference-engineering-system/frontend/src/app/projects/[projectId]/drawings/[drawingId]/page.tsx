"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, Star } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { DrawingVersionStatusBadge } from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import { documentsApi, type DrawingOut, type DrawingVersionOut } from "@/lib/api-client";

export default function DrawingDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; drawingId: string }>;
}) {
  const { projectId, drawingId } = use(params);
  const { session } = useRequireSession();
  const [drawing, setDrawing] = useState<DrawingOut | null>(null);
  const [versions, setVersions] = useState<DrawingVersionOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);
    const did = Number(drawingId);
    Promise.all([documentsApi.get(pid, did), documentsApi.versions(pid, did)]).then(
      ([drawingDetail, versionList]) => {
        setDrawing(drawingDetail);
        setVersions(
          [...versionList].sort(
            (a, b) => new Date(b.issuance_date).getTime() - new Date(a.issuance_date).getTime()
          )
        );
      }
    );
  }, [session, projectId, drawingId]);

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title={drawing ? `${drawing.sheet_number} — ${drawing.title}` : "Drawing Detail"}
        description={drawing ? `Discipline ${drawing.discipline_code}` : undefined}
        actions={
          <Link href={`/projects/${projectId}/drawings`}>
            <Button variant="outline" size="sm">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to register
            </Button>
          </Link>
        }
      />

      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Revision timeline</CardTitle>
          </CardHeader>
          <CardContent>
            {versions === null ? (
              <Skeleton className="h-48 w-full" />
            ) : versions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No versions recorded yet.</p>
            ) : (
              <ol className="flex flex-col gap-4">
                {versions.map((version) => {
                  const isCurrent = drawing?.current_version_id === version.id;
                  return (
                    <li
                      key={version.id}
                      className="relative border-l-2 border-muted pl-5 last:border-transparent"
                    >
                      <span className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-primary" />
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold">{version.revision_label}</span>
                        <DrawingVersionStatusBadge status={version.status} />
                        {isCurrent && (
                          <span className="flex items-center gap-1 text-xs font-medium text-amber-600">
                            <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
                            Current
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">{version.issuance_date}</span>
                      </div>
                      {version.superseded_by_id != null && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Superseded by version #{version.superseded_by_id}
                        </p>
                      )}
                      {version.revision_clouds.length > 0 && (
                        <ul className="mt-2 flex flex-col gap-1">
                          {version.revision_clouds.map((cloud, i) => (
                            <li key={i} className="text-sm">
                              <span className="font-medium">Δ{cloud.delta_number}</span>{" "}
                              <span className="text-muted-foreground">({cloud.area})</span>{" "}
                              {cloud.description}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}
              </ol>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
