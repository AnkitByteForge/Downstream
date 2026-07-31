"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

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
import { documentsApi, type DrawingOut } from "@/lib/api-client";

export default function DrawingRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [drawings, setDrawings] = useState<DrawingOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    documentsApi.list(Number(projectId)).then(setDrawings);
  }, [session, projectId]);

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Drawing Register"
        description="Sheets and their current issued revision."
      />
      <div className="p-6">
        {drawings === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Sheet</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="w-32">Discipline</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {drawings.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} className="py-8 text-center text-muted-foreground">
                      No drawings on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {drawings.map((drawing) => (
                  <TableRow key={drawing.id}>
                    <TableCell className="font-medium">
                      <Link href={`/projects/${projectId}/drawings/${drawing.id}`} className="block">
                        {drawing.sheet_number}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/projects/${projectId}/drawings/${drawing.id}`} className="block">
                        {drawing.title}
                      </Link>
                    </TableCell>
                    <TableCell>{drawing.discipline_code}</TableCell>
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
