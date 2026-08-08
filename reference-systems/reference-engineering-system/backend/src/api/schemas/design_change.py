from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DesignChangeOut(BaseModel):
    id: int
    project_id: int
    number: str
    display_number: str
    type: str
    status: str
    change_reason: str | None
    discipline_code: str | None
    source_rfi_id: int | None
    ball_in_court: str
    affected_drawing_version_ids: list[int]
    affected_spec_section_ids: list[int]
    location_ids: list[int]
    superseded_by_id: int | None
    issued_at: datetime | None
    acknowledged_at: datetime | None
    voided_at: datetime | None
