"use client";

import { use, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useRequireSession } from "@/lib/auth/use-session";
import {
  specDivisionsApi,
  specSectionsApi,
  submittalRequirementsApi,
  type SpecDivisionOut,
  type SpecSectionOut,
  type SubmittalRequirementOut,
} from "@/lib/api-client";

export default function SpecificationBrowserPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { session } = useRequireSession();
  const [divisions, setDivisions] = useState<SpecDivisionOut[] | null>(null);
  const [sections, setSections] = useState<SpecSectionOut[]>([]);
  const [requirements, setRequirements] = useState<SubmittalRequirementOut[]>([]);

  useEffect(() => {
    if (!session) return;
    const pid = Number(projectId);

    async function load() {
      const [divisionList, sectionList, requirementList] = await Promise.all([
        specDivisionsApi.list(),
        specSectionsApi.list(pid),
        submittalRequirementsApi.list(pid),
      ]);
      setDivisions(divisionList);
      setSections(sectionList);
      setRequirements(requirementList);
    }

    void load();
  }, [session, projectId]);

  const sectionsByDivision = new Map<string, SpecSectionOut[]>();
  for (const section of sections) {
    const list = sectionsByDivision.get(section.division_number) ?? [];
    list.push(section);
    sectionsByDivision.set(section.division_number, list);
  }

  const requirementsBySection = new Map<number, SubmittalRequirementOut[]>();
  for (const req of requirements) {
    const list = requirementsBySection.get(req.spec_section_id) ?? [];
    list.push(req);
    requirementsBySection.set(req.spec_section_id, list);
  }

  const usedDivisions = (divisions ?? []).filter((d) => sectionsByDivision.has(d.number));

  return (
    <AppShell session={session} projectId={Number(projectId)}>
      <PageHeader
        title="Specification Browser"
        description="CSI MasterFormat divisions and sections, with each section's submittal register."
      />
      <div className="flex flex-col gap-4 p-6">
        {divisions === null ? (
          <Skeleton className="h-64 w-full" />
        ) : usedDivisions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No spec sections on this project yet.</p>
        ) : (
          usedDivisions.map((division) => (
            <Card key={division.number}>
              <CardHeader>
                <CardTitle className="text-base">
                  Division {division.number} — {division.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {(sectionsByDivision.get(division.number) ?? []).map((section) => (
                  <div key={section.id} className="rounded-md border p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">
                        {section.number} — {section.title}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(requirementsBySection.get(section.id) ?? []).map((req) => (
                        <Badge key={req.id} variant="secondary" className="font-normal">
                          {req.submittal_type} ({req.category})
                        </Badge>
                      ))}
                      {(requirementsBySection.get(section.id) ?? []).length === 0 && (
                        <span className="text-xs text-muted-foreground">
                          No submittal register entries.
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </AppShell>
  );
}
