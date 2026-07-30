"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderKanban } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRequireSession } from "@/lib/auth/use-session";
import { projectsApi, type ProjectOut } from "@/lib/api-client";

export default function ProjectsPage() {
  const { session } = useRequireSession();
  const [projects, setProjects] = useState<ProjectOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    projectsApi.list().then(setProjects);
  }, [session]);

  return (
    <AppShell session={session} projectId={session?.project_id}>
      <PageHeader title="Project Explorer" description="Every project this account can see." />
      <div className="grid grid-cols-1 gap-4 p-6 md:grid-cols-2 lg:grid-cols-3">
        {projects === null &&
          Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28 w-full" />)}
        {projects?.map((project) => (
          <Link key={project.id} href={`/projects/${project.id}/rfis`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="flex h-9 w-9 items-center justify-center rounded bg-blue-600/10 text-blue-700 dark:text-blue-400">
                  <FolderKanban className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-base">{project.name}</CardTitle>
                  <p className="text-xs text-muted-foreground">{project.spec_format}</p>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">Project #{project.id}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
