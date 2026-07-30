from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RFIOut(BaseModel):
    """Field names deliberately mirror the real Procore RFI resource shape
    (Reference Execution Trace Phase 1.2) — id is the opaque real key,
    display_number the separate editable label, never collapsed."""

    id: int
    project_id: int
    number: str
    display_number: str
    subject: str
    question: str | None
    response: str | None
    status: str
    ball_in_court: str
    cost_impact_flag: str | None
    cost_code: str | None
    discipline_code: str | None
    spawned_change_id: int | None
    raw_document_ref: str | None
    drawing_version_ids: list[int]
    spec_section_ids: list[int]
    location_ids: list[int]
    closed_at: datetime | None


class RespondToRFIIn(BaseModel):
    response_text: str
    manager_user_id: int


class CloseRFIIn(BaseModel):
    response_text: str | None = None
