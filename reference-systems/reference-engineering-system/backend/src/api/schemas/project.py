from __future__ import annotations

from pydantic import BaseModel


class ProjectOut(BaseModel):
    id: int
    name: str
    spec_format: str


class DisciplineOut(BaseModel):
    code: str
    name: str
