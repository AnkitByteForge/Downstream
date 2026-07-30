// Mirrors the backend's Pydantic response schemas (api/schemas/*.py) field for
// field — this file is the frontend/backend contract's single source of truth
// on the TypeScript side. Keep in sync by hand for RES-1; a generated client
// from the backend's OpenAPI schema is reasonable follow-up work, not required
// to satisfy "consume the system's own REST API, do not bypass the backend."

export interface SessionOut {
  user_id: number;
  project_id: number;
  role: string;
}

export interface ProjectOut {
  id: number;
  name: string;
  spec_format: string;
}

export interface LocationOut {
  id: number;
  project_id: number;
  parent_id: number | null;
  tier_level: number;
  name: string;
  type: string;
}

export interface SpecSectionOut {
  id: number;
  project_id: number;
  division_number: string;
  number: string;
  title: string;
  substitution_policy: string | null;
}

export interface RevisionCloudOut {
  area: string;
  delta_number: number;
  description: string;
}

export interface DrawingOut {
  id: number;
  project_id: number;
  sheet_number: string;
  title: string;
  discipline_code: string;
  current_version_id: number | null;
}

export interface DrawingVersionOut {
  id: number;
  drawing_id: number;
  revision_label: string;
  issuance_date: string;
  status: string;
  discipline_code: string;
  superseded_by_id: number | null;
  revision_clouds: RevisionCloudOut[];
  location_ids: number[];
}

export type RFIStatus = "DRAFT" | "OPEN" | "RESPONDED" | "CLOSED";

export interface RFIOut {
  id: number;
  project_id: number;
  number: string;
  display_number: string;
  subject: string;
  question: string | null;
  response: string | null;
  status: RFIStatus;
  ball_in_court: string;
  cost_impact_flag: string | null;
  cost_code: string | null;
  discipline_code: string | null;
  spawned_change_id: number | null;
  raw_document_ref: string | null;
  drawing_version_ids: number[];
  spec_section_ids: number[];
  location_ids: number[];
  closed_at: string | null;
}
