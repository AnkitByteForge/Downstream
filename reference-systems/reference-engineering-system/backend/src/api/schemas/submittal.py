from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class SubmittalOut(BaseModel):
    id: int
    project_id: int
    number: str
    spec_section_id: int
    package_id: int | None
    vendor_id: int | None
    commitment_id: int | None
    submittal_type: str
    category: str
    lead_time_days: int | None
    required_on_site_date: date | None
    is_long_lead: bool


class SubmittalRevisionOut(BaseModel):
    id: int
    submittal_id: int
    rev_label: str
    review_status_id: int
    review_status_code: str
    review_status_label: str
    gates_procurement: bool
    ball_in_court: str
    equipment_tag: str | None
    manufacturer: str | None
    model: str | None
    capacity_value: float | None
    capacity_unit: str | None
    submitted_at: datetime | None
    disposed_by_user_id: int | None
    disposition_at: datetime | None
    drawing_version_ids: list[int]
    location_ids: list[int]


class SubmittalReviewStatusOut(BaseModel):
    id: int
    project_id: int
    code: str
    label: str
    gates_procurement: bool
    is_terminal: bool
    sort_order: int


class RecordSubmittalDispositionIn(BaseModel):
    review_status_code: str
    disposed_by_user_id: int
    comments: str | None = None


class SubmittalRequirementOut(BaseModel):
    id: int
    project_id: int
    spec_section_id: int
    submittal_type: str
    category: str
