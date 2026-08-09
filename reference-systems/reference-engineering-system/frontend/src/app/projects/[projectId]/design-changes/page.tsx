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
import {
  BallInCourtBadge,
  DesignChangeStatusBadge,
} from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  designChangesApi,
  documentsApi,
  rfisApi,
  specSectionsApi,
  type DesignChangeOut,
  type DrawingVersionOut,
  type RFIOut,
  type SpecSectionOut,
} from "@/lib/api-client";

export default function DesignChangeRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [changes, setChanges] = useState<DesignChangeOut[] | null>(null);
  const [rfis, setRfis] = useState<RFIOut[]>([]);
  const [specSections, setSpecSections] = useState<SpecSectionOut[]>([]);
  const [affectedVersions, setAffectedVersions] = useState<Map<number, DrawingVersionOut>>(
    new Map()
  );

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);

    async function load() {
      const [changeList, rfiList, sections] = await Promise.all([
        designChangesApi.list(pid),
        rfisApi.list(pid),
        specSectionsApi.list(pid),
      ]);
      setChanges(changeList);
      setRfis(rfiList);
      setSpecSections(sections);
      const versionIds = [...new Set(changeList.flatMap((c) => c.affected_drawing_version_ids))];
      const versions = await Promise.all(versionIds.map((vId) => documentsApi.getVersion(pid, vId)));
      setAffectedVersions(new Map(versions.map((v) => [v.id, v])));
    }

    void load();
  }, [session, projectId]);

  const rfiLookup = new Map(rfis.map((r) => [r.id, r]));
  const specSectionLookup = new Map(specSections.map((s) => [s.id, s]));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Design Changes"
        description="Engineering-authorization instruments (ASI / CCD / Bulletin) and their affected drawings."
      />
      <div className="p-6">
        {changes === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-28">Number</TableHead>
                  <TableHead className="w-28">Type</TableHead>
                  <TableHead className="w-36">Ball in court</TableHead>
                  <TableHead className="w-40">Status</TableHead>
                  <TableHead>Affects</TableHead>
                  <TableHead className="w-36">Source RFI</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {changes.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                      No design changes on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {changes.map((change) => {
                  const affected = change.affected_drawing_version_ids
                    .map((vId) => affectedVersions.get(vId))
                    .filter((v): v is DrawingVersionOut => Boolean(v))
                    .map((v) => `${v.revision_label}`)
                    .join(", ");
                  const specNumbers = change.affected_spec_section_ids
                    .map((sId) => specSectionLookup.get(sId)?.number)
                    .filter((n): n is string => Boolean(n))
                    .join(", ");
                  const sourceRfi =
                    change.source_rfi_id != null ? rfiLookup.get(change.source_rfi_id) : null;
                  return (
                    <TableRow key={change.id}>
                      <TableCell className="font-medium">
                        <Link href={`/projects/${projectId}/design-changes/${change.id}`} className="block">
                          {change.display_number}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link href={`/projects/${projectId}/design-changes/${change.id}`} className="block">
                          {change.type}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <BallInCourtBadge ballInCourt={change.ball_in_court} />
                      </TableCell>
                      <TableCell>
                        <DesignChangeStatusBadge status={change.status} />
                      </TableCell>
                      <TableCell>
                        <Link href={`/projects/${projectId}/design-changes/${change.id}`} className="block">
                          {[affected, specNumbers].filter(Boolean).join(" · ") || "—"}
                        </Link>
                      </TableCell>
                      <TableCell>
                        {sourceRfi ? (
                          <Link
                            href={`/projects/${projectId}/rfis/${sourceRfi.id}`}
                            className="block text-blue-600 hover:underline dark:text-blue-400"
                          >
                            {sourceRfi.display_number}
                          </Link>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
