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

export type ActivityStatus = "SENT" | "FAILED";

export interface ActivityEntryOut {
  id: number;
  project_id: number;
  resource_name: string;
  resource_id: number;
  event_type: string;
  occurred_at: string;
  status: ActivityStatus;
  dispatched_at: string;
}

export interface SpecDivisionOut {
  number: string;
  title: string;
}

export interface VendorOut {
  id: number;
  project_id: number;
  name: string;
}

export interface SubmittalOut {
  id: number;
  project_id: number;
  number: string;
  spec_section_id: number;
  package_id: number | null;
  vendor_id: number | null;
  commitment_id: number | null;
  submittal_type: string;
  category: string;
  lead_time_days: number | null;
  required_on_site_date: string | null;
  is_long_lead: boolean;
}

export interface SubmittalRevisionOut {
  id: number;
  submittal_id: number;
  rev_label: string;
  review_status_id: number;
  review_status_code: string;
  review_status_label: string;
  gates_procurement: boolean;
  ball_in_court: string;
  equipment_tag: string | null;
  manufacturer: string | null;
  model: string | null;
  capacity_value: number | null;
  capacity_unit: string | null;
  fla_value: number | null;
  fla_unit: string | null;
  submitted_at: string | null;
  disposed_by_user_id: number | null;
  disposition_at: string | null;
  drawing_version_ids: number[];
  location_ids: number[];
}

export interface SubmittalRequirementOut {
  id: number;
  project_id: number;
  spec_section_id: number;
  submittal_type: string;
  category: string;
}
