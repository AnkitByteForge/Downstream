from __future__ import annotations

from pydantic import BaseModel


class SpecDivisionOut(BaseModel):
    number: str
    title: str


class SpecSectionOut(BaseModel):
    id: int
    project_id: int
    division_number: str
    number: str
    title: str
    substitution_policy: str | None
