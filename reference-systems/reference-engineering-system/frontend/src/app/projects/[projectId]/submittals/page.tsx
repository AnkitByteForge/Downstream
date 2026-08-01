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
import { BallInCourtBadge, LongLeadBadge, SubmittalStatusBadge } from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  specSectionsApi,
  submittalsApi,
  type SpecSectionOut,
  type SubmittalOut,
  type SubmittalRevisionOut,
} from "@/lib/api-client";

interface Row {
  submittal: SubmittalOut;
  latestRevision: SubmittalRevisionOut | null;
}

export default function SubmittalRegisterPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [specSections, setSpecSections] = useState<SpecSectionOut[]>([]);

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);

    async function load() {
      const [submittals, sections] = await Promise.all([
        submittalsApi.list(pid),
        specSectionsApi.list(pid),
      ]);
      setSpecSections(sections);
      const withRevisions = await Promise.all(
        submittals.map(async (submittal) => {
          const revisions = await submittalsApi.revisions(pid, submittal.id);
          return { submittal, latestRevision: revisions.at(-1) ?? null };
        })
      );
      setRows(withRevisions);
    }

    void load();
  }, [session, projectId]);

  const specSectionLookup = new Map(specSections.map((s) => [s.id, s]));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Submittal Register"
        description="Review status gates fabrication and procurement release."
      />
      <div className="p-6">
        {rows === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Number</TableHead>
                  <TableHead>Spec Section</TableHead>
                  <TableHead className="w-32">Ball in court</TableHead>
                  <TableHead className="w-44">Status</TableHead>
                  <TableHead className="w-28">Long lead</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      No submittals on this project yet.
                    </TableCell>
                  </TableRow>
                )}
                {rows.map(({ submittal, latestRevision }) => {
                  const section = specSectionLookup.get(submittal.spec_section_id);
                  return (
                    <TableRow key={submittal.id}>
                      <TableCell className="font-medium">
                        <Link href={`/projects/${projectId}/submittals/${submittal.id}`} className="block">
                          SUB-{submittal.number}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link href={`/projects/${projectId}/submittals/${submittal.id}`} className="block">
                          {section ? `${section.number} — ${section.title}` : submittal.spec_section_id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        {latestRevision && <BallInCourtBadge ballInCourt={latestRevision.ball_in_court} />}
                      </TableCell>
                      <TableCell>
                        {latestRevision && (
                          <SubmittalStatusBadge
                            label={latestRevision.review_status_label}
                            gatesProcurement={latestRevision.gates_procurement}
                          />
                        )}
                      </TableCell>
                      <TableCell>{submittal.is_long_lead && <LongLeadBadge />}</TableCell>
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
