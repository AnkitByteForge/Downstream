from __future__ import annotations

from pydantic import BaseModel


class VendorOut(BaseModel):
    id: int
    project_id: int
    name: str


class CommitmentOut(BaseModel):
    id: int
    project_id: int
    vendor_id: int
    cost_code: str
    description: str
    amount: float
    spec_section_id: int | None
