"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileQuestion, FolderKanban } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RFIStatusBadge } from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import { projectsApi, rfisApi, type ProjectOut, type RFIOut } from "@/lib/api-client";

export default function DashboardPage() {
  const { session, loading: sessionLoading } = useRequireSession();
  const [project, setProject] = useState<ProjectOut | null>(null);
  const [rfis, setRfis] = useState<RFIOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    Promise.all([projectsApi.get(session.project_id), rfisApi.list(session.project_id)]).then(
      ([proj, rfiList]) => {
        setProject(proj);
        setRfis(rfiList);
        setLoading(false);
      }
    );
  }, [session]);

  const openRfis = rfis.filter((r) => r.status !== "CLOSED");
  const closedRfis = rfis.filter((r) => r.status === "CLOSED");

  return (
    <AppShell session={session} projectId={session?.project_id}>
      <PageHeader
        title="Dashboard"
        description={project ? project.name : sessionLoading ? "Loading..." : undefined}
      />
      <div className="grid grid-cols-1 gap-4 p-6 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Open RFIs</CardTitle>
            <FileQuestion className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-8 w-12" /> : <div className="text-2xl font-bold">{openRfis.length}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Closed RFIs</CardTitle>
            <FileQuestion className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-8 w-12" /> : <div className="text-2xl font-bold">{closedRfis.length}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Project</CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-lg font-semibold">{project?.name}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="px-6 pb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent RFI activity</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {loading && <Skeleton className="h-10 w-full" />}
            {!loading && rfis.length === 0 && (
              <p className="text-sm text-muted-foreground">No RFIs on this project yet.</p>
            )}
            {rfis.map((rfi) => (
              <Link
                key={rfi.id}
                href={`/projects/${rfi.project_id}/rfis/${rfi.id}`}
                className="flex items-center justify-between rounded-md border px-4 py-3 text-sm transition-colors hover:bg-muted/50"
              >
                <div className="flex flex-col">
                  <span className="font-medium">{rfi.display_number}</span>
                  <span className="text-muted-foreground">{rfi.subject}</span>
                </div>
                <RFIStatusBadge status={rfi.status} />
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
