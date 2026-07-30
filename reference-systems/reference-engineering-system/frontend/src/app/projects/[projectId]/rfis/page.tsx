"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { RFIStatusBadge, BallInCourtBadge } from "@/components/status-badge";
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
import { rfisApi, type RFIOut } from "@/lib/api-client";

export default function RFIRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [rfis, setRfis] = useState<RFIOut[] | null>(null);

  useEffect(() => {
    if (!session) return;
    rfisApi.list(Number(projectId)).then(setRfis);
  }, [session, projectId]);

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="RFI Register"
        description="Requests for Information — ball-in-court routing drives who acts next."
      />
      <div className="p-6">
        {rfis === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-28">Number</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead className="w-32">Discipline</TableHead>
                  <TableHead className="w-32">Ball in court</TableHead>
                  <TableHead className="w-28">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rfis.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      No RFIs on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {rfis.map((rfi) => (
                  <TableRow key={rfi.id} className="cursor-pointer">
                    <TableCell className="font-medium">
                      <Link href={`/projects/${projectId}/rfis/${rfi.id}`} className="block">
                        {rfi.display_number}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/projects/${projectId}/rfis/${rfi.id}`} className="block">
                        {rfi.subject}
                      </Link>
                    </TableCell>
                    <TableCell>{rfi.discipline_code ?? "—"}</TableCell>
                    <TableCell>
                      <BallInCourtBadge ballInCourt={rfi.ball_in_court} />
                    </TableCell>
                    <TableCell>
                      <RFIStatusBadge status={rfi.status} />
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
