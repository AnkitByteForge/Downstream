"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, TriangleAlert } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { BallInCourtBadge, SubmittalStatusBadge } from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  specSectionsApi,
  submittalsApi,
  vendorsApi,
  type SpecSectionOut,
  type SubmittalOut,
  type SubmittalRevisionOut,
  type VendorOut,
} from "@/lib/api-client";

export default function SubmittalDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; submittalId: string }>;
}) {
  const { projectId, submittalId } = use(params);
  const { session } = useRequireSession();
  const [submittal, setSubmittal] = useState<SubmittalOut | null>(null);
  const [revisions, setRevisions] = useState<SubmittalRevisionOut[] | null>(null);
  const [specSection, setSpecSection] = useState<SpecSectionOut | null>(null);
  const [vendor, setVendor] = useState<VendorOut | null>(null);

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);
    const sid = Number(submittalId);

    async function load() {
      const [submittalDetail, revisionList, sections, vendors] = await Promise.all([
        submittalsApi.get(pid, sid),
        submittalsApi.revisions(pid, sid),
        specSectionsApi.list(pid),
        vendorsApi.list(pid),
      ]);
      setSubmittal(submittalDetail);
      setRevisions([...revisionList].reverse());
      setSpecSection(sections.find((s) => s.id === submittalDetail.spec_section_id) ?? null);
      setVendor(vendors.find((v) => v.id === submittalDetail.vendor_id) ?? null);
    }

    void load();
  }, [session, projectId, submittalId]);

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title={submittal ? `SUB-${submittal.number}` : "Submittal Detail"}
        description={specSection ? `${specSection.number} — ${specSection.title}` : undefined}
        actions={
          <Link href={`/projects/${projectId}/submittals`}>
            <Button variant="outline" size="sm">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to register
            </Button>
          </Link>
        }
      />

      {!submittal || revisions === null ? (
        <div className="p-6">
          <Skeleton className="h-96 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 p-6 lg:grid-cols-3">
          <div className="flex flex-col gap-4 lg:col-span-2">
            {submittal.is_long_lead && (
              <Card className="border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40">
                <CardContent className="flex items-center gap-3 py-4">
                  <TriangleAlert className="h-5 w-5 text-amber-600" />
                  <div className="text-sm">
                    <span className="font-semibold">Long-lead item.</span> Lead time (
                    {submittal.lead_time_days} days) exceeds the days remaining to the required
                    on-site date ({submittal.required_on_site_date}).
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Revision history</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="flex flex-col gap-4">
                  {revisions.map((revision) => (
                    <li key={revision.id} className="relative border-l-2 border-muted pl-5 last:border-transparent">
                      <span className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-primary" />
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold">{revision.rev_label}</span>
                        <SubmittalStatusBadge
                          label={revision.review_status_label}
                          gatesProcurement={revision.gates_procurement}
                        />
                        <BallInCourtBadge ballInCourt={revision.ball_in_court} />
                        {revision.disposition_at && (
                          <span className="text-xs text-muted-foreground">
                            {new Date(revision.disposition_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      {(revision.equipment_tag || revision.manufacturer || revision.model) && (
                        <p className="mt-1 text-sm text-muted-foreground">
                          {revision.equipment_tag} — {revision.manufacturer} {revision.model}
                          {revision.capacity_value != null &&
                            ` — MCA ${revision.capacity_value} ${revision.capacity_unit ?? ""}`}
                          {revision.fla_value != null &&
                            ` / FLA ${revision.fla_value} ${revision.fla_unit ?? ""}`}
                        </p>
                      )}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>

          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Details</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Vendor</span>
                  <span>{vendor?.name ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <span>{submittal.submittal_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Category</span>
                  <span>{submittal.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Lead time</span>
                  <span>{submittal.lead_time_days ? `${submittal.lead_time_days} days` : "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Required on site</span>
                  <span>{submittal.required_on_site_date ?? "—"}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppShell>
  );
}
