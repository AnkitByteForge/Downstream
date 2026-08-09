"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, BookOpen, MapPin, FileStack } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import {
  BallInCourtBadge,
  DesignChangeStatusBadge,
} from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  designChangesApi,
  documentsApi,
  locationsApi,
  rfisApi,
  specSectionsApi,
  type DesignChangeOut,
  type DrawingVersionOut,
  type LocationOut,
  type RFIOut,
  type SpecSectionOut,
} from "@/lib/api-client";

export default function DesignChangeDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; changeId: string }>;
}) {
  const { projectId, changeId } = use(params);
  const { session } = useRequireSession();

  const [change, setChange] = useState<DesignChangeOut | null>(null);
  const [specSections, setSpecSections] = useState<SpecSectionOut[]>([]);
  const [locations, setLocations] = useState<LocationOut[]>([]);
  const [rfis, setRfis] = useState<RFIOut[]>([]);
  const [drawingVersions, setDrawingVersions] = useState<DrawingVersionOut[]>([]);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    const pid = Number(projectId);

    async function fetchAll() {
      const [changeDetail, sections, locs, rfiList] = await Promise.all([
        designChangesApi.get(pid, Number(changeId)),
        specSectionsApi.list(pid),
        locationsApi.list(pid),
        rfisApi.list(pid),
      ]);
      const versions = await Promise.all(
        changeDetail.affected_drawing_version_ids.map((vId) =>
          documentsApi.getVersion(pid, vId)
        )
      );
      if (cancelled) return;
      setChange(changeDetail);
      setSpecSections(sections);
      setLocations(locs);
      setRfis(rfiList);
      setDrawingVersions(versions);
    }

    void fetchAll();
    return () => {
      cancelled = true;
    };
  }, [session, projectId, changeId]);

  const specSectionLookup = new Map(specSections.map((s) => [s.id, s]));
  const locationLookup = new Map(locations.map((l) => [l.id, l]));
  const rfiLookup = new Map(rfis.map((r) => [r.id, r]));
  const sourceRfi = change?.source_rfi_id != null ? rfiLookup.get(change.source_rfi_id) : null;

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title={change ? `${change.display_number}` : "Design Change"}
        description={change?.change_reason ?? undefined}
        actions={
          <Link href={`/projects/${projectId}/design-changes`}>
            <Button variant="outline" size="sm">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to register
            </Button>
          </Link>
        }
      />

      {!change ? (
        <div className="p-6">
          <Skeleton className="h-96 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 p-6 lg:grid-cols-3">
          <div className="flex flex-col gap-4 lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{change.type} — {change.change_reason}</CardTitle>
                <div className="flex items-center gap-2">
                  <BallInCourtBadge ballInCourt={change.ball_in_court} />
                  <DesignChangeStatusBadge status={change.status} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-4">
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Authorization timeline
                    </h3>
                    <ol className="flex flex-col gap-3">
                      <li className="relative border-l-2 border-muted pl-5">
                        <span className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-muted-foreground/60" />
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">DRAFT</span>
                          <span className="text-xs text-muted-foreground">Drafted</span>
                        </div>
                      </li>
                      <li className="relative border-l-2 border-muted pl-5 last:border-transparent">
                        <span
                          className={`absolute -left-[7px] top-1 h-3 w-3 rounded-full ${
                            change.issued_at ? "bg-primary" : "bg-muted"
                          }`}
                        />
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">ISSUED</span>
                          {change.issued_at && (
                            <span className="text-xs text-muted-foreground">
                              {new Date(change.issued_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </li>
                      {change.status !== "DRAFT" && (
                        <li className="relative border-l-2 border-muted pl-5 last:border-transparent">
                          <span
                            className={`absolute -left-[7px] top-1 h-3 w-3 rounded-full ${
                              change.acknowledged_at ? "bg-primary" : "bg-muted"
                            }`}
                          />
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">ACKNOWLEDGED</span>
                            {change.acknowledged_at && (
                              <span className="text-xs text-muted-foreground">
                                {new Date(change.acknowledged_at).toLocaleString()}
                              </span>
                            )}
                          </div>
                        </li>
                      )}
                      {change.superseded_by_id != null && (
                        <li className="relative pl-5">
                          <span className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-muted" />
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">SUPERSEDED</span>
                            <span className="text-xs text-muted-foreground">
                              by change #{change.superseded_by_id}
                            </span>
                          </div>
                        </li>
                      )}
                      {change.voided_at && (
                        <li className="relative pl-5">
                          <span className="absolute -left-[7px] top-1 h-3 w-3 rounded-full bg-red-500" />
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">VOID</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(change.voided_at).toLocaleString()}
                            </span>
                          </div>
                        </li>
                      )}
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Affected drawing revisions</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {drawingVersions.length === 0 && (
                  <p className="text-sm text-muted-foreground">No drawing revisions affected.</p>
                )}
                {drawingVersions.map((v) => (
                  <Link
                    key={v.id}
                    href={`/projects/${projectId}/drawings/${v.drawing_id}`}
                    className="flex items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-muted"
                  >
                    <span className="font-medium">{v.revision_label}</span>
                    <span className="text-muted-foreground">{v.issuance_date}</span>
                    <span className="text-muted-foreground">{v.status}</span>
                  </Link>
                ))}
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
                  <span className="text-muted-foreground">Type</span>
                  <span>{change.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Discipline</span>
                  <span>{change.discipline_code ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Ball in court</span>
                  <span className="capitalize">{change.ball_in_court}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Source RFI</span>
                  {sourceRfi ? (
                    <Link
                      href={`/projects/${projectId}/rfis/${sourceRfi.id}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {sourceRfi.display_number}
                    </Link>
                  ) : (
                    <span>—</span>
                  )}
                </div>
                <Separator />
                <div className="flex items-start gap-2">
                  <FileStack className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Affected drawings
                    </span>
                    {change.affected_drawing_version_ids.length === 0 && <span>—</span>}
                    {change.affected_drawing_version_ids.map((vId) => {
                      const version = drawingVersions.find((v) => v.id === vId);
                      if (version) {
                        return (
                          <Link
                            key={vId}
                            href={`/projects/${projectId}/drawings/${version.drawing_id}`}
                            className="text-blue-600 hover:underline dark:text-blue-400"
                          >
                            {version.revision_label}
                          </Link>
                        );
                      }
                      return <span key={vId}>{`#${vId}`}</span>;
                    })}
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <BookOpen className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Spec sections
                    </span>
                    {change.affected_spec_section_ids.length === 0 && <span>—</span>}
                    {change.affected_spec_section_ids.map((sId) => (
                      <span key={sId}>
                        {specSectionLookup.get(sId)?.number ?? `#${sId}`}
                        {" "}
                        {specSectionLookup.get(sId)?.title ?? ""}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <MapPin className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Locations
                    </span>
                    {change.location_ids.map((id) => (
                      <span key={id}>{locationLookup.get(id)?.name ?? `#${id}`}</span>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppShell>
  );
}
