from __future__ import annotations

from pydantic import BaseModel


class VendorOut(BaseModel):
    id: int
    name: str
    qualification_status: str
    performance_score: float | None


class VendorScopeViewOut(BaseModel):
    id: int
    vendor_id: int
    company_code: str | None
    purchasing_org: str | None
    blocked: bool
    purchasing_terms: dict


class CreateVendorRequest(BaseModel):
    name: str


class CreateVendorScopeViewRequest(BaseModel):
    company_code: str | None = None
    purchasing_org: str | None = None
    blocked: bool = False
