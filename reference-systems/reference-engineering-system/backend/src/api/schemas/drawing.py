from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class RevisionCloudOut(BaseModel):
    area: str
    delta_number: int
    description: str
    source_evidence_ref: str | None = None


class RevisionCloudIn(BaseModel):
    area: str
    delta_number: int
    description: str
    source_evidence_ref: str | None = None


class CreateDrawingIn(BaseModel):
    sheet_number: str
    title: str
    discipline_code: str


class CreateDrawingVersionIn(BaseModel):
    revision_label: str
    discipline_code: str
    revision_clouds: list[RevisionCloudIn] = []


class DrawingOut(BaseModel):
    id: int
    project_id: int
    sheet_number: str
    title: str
    discipline_code: str
    current_version_id: int | None


class DrawingVersionOut(BaseModel):
    id: int
    drawing_id: int
    revision_label: str
    issuance_date: date
    status: str
    discipline_code: str
    superseded_by_id: int | None
    revision_clouds: list[RevisionCloudOut]
    location_ids: list[int]
