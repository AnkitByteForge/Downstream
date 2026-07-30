"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, FileText, MapPin, BookOpen } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { RFIStatusBadge, BallInCourtBadge } from "@/components/status-badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  documentsApi,
  locationsApi,
  rfisApi,
  specSectionsApi,
  type DrawingVersionOut,
  type LocationOut,
  type RFIOut,
  type SpecSectionOut,
} from "@/lib/api-client";

export default function RFIDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; rfiId: string }>;
}) {
  const { projectId, rfiId } = use(params);
  const { session } = useRequireSession();

  const [rfi, setRfi] = useState<RFIOut | null>(null);
  const [specSections, setSpecSections] = useState<SpecSectionOut[]>([]);
  const [locations, setLocations] = useState<LocationOut[]>([]);
  const [drawingVersions, setDrawingVersions] = useState<DrawingVersionOut[]>([]);
  const [busy, setBusy] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    const pid = Number(projectId);

    async function fetchAll() {
      const [rfiDetail, sections, locs] = await Promise.all([
        rfisApi.get(pid, Number(rfiId)),
        specSectionsApi.list(pid),
        locationsApi.list(pid),
      ]);
      const versions = await Promise.all(
        rfiDetail.drawing_version_ids.map((vId) => documentsApi.getVersion(pid, vId))
      );
      if (cancelled) return;
      setRfi(rfiDetail);
      setSpecSections(sections);
      setLocations(locs);
      setDrawingVersions(versions);
    }

    void fetchAll();
    return () => {
      cancelled = true;
    };
  }, [session, projectId, rfiId, reloadToken]);

  async function handleClose() {
    if (!rfi) return;
    setBusy(true);
    try {
      await rfisApi.close(Number(projectId), rfi.id);
      setReloadToken((t) => t + 1);
    } finally {
      setBusy(false);
    }
  }

  const specSectionLookup = new Map(specSections.map((s) => [s.id, s]));
  const locationLookup = new Map(locations.map((l) => [l.id, l]));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title={rfi ? `${rfi.display_number}` : "RFI Detail"}
        description={rfi?.subject}
        actions={
          <Link href={`/projects/${projectId}/rfis`}>
            <Button variant="outline" size="sm">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to register
            </Button>
          </Link>
        }
      />

      {!rfi ? (
        <div className="p-6">
          <Skeleton className="h-96 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 p-6 lg:grid-cols-3">
          <div className="flex flex-col gap-4 lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{rfi.subject}</CardTitle>
                <div className="flex items-center gap-2">
                  <BallInCourtBadge ballInCourt={rfi.ball_in_court} />
                  <RFIStatusBadge status={rfi.status} />
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {rfi.question && (
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Question
                    </h3>
                    <p className="text-sm">{rfi.question}</p>
                  </div>
                )}
                {rfi.response && (
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Response
                    </h3>
                    <p className="text-sm">{rfi.response}</p>
                  </div>
                )}
                {rfi.raw_document_ref && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>{rfi.raw_document_ref}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Cited drawing revisions</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {drawingVersions.length === 0 && (
                  <p className="text-sm text-muted-foreground">No drawing revisions cited.</p>
                )}
                {drawingVersions.map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                  >
                    <span className="font-medium">{v.revision_label}</span>
                    <span className="text-muted-foreground">{v.issuance_date}</span>
                    <span className="text-muted-foreground">{v.status}</span>
                  </div>
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
                  <span className="text-muted-foreground">Discipline</span>
                  <span>{rfi.discipline_code ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Cost impact</span>
                  <span>{rfi.cost_impact_flag ?? "Not flagged"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Closed at</span>
                  <span>{rfi.closed_at ? new Date(rfi.closed_at).toLocaleString() : "—"}</span>
                </div>
                <Separator />
                <div className="flex items-start gap-2">
                  <BookOpen className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Spec sections
                    </span>
                    {rfi.spec_section_ids.map((id) => (
                      <span key={id}>{specSectionLookup.get(id)?.number ?? `#${id}`}</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <MapPin className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Locations
                    </span>
                    {rfi.location_ids.map((id) => (
                      <span key={id}>{locationLookup.get(id)?.name ?? `#${id}`}</span>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {rfi.status !== "CLOSED" && (
              <Button onClick={handleClose} disabled={busy}>
                {busy ? "Closing..." : "Close RFI"}
              </Button>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
