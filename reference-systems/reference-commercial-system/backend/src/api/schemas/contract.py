from __future__ import annotations

from pydantic import BaseModel

from api.schemas.org_scope import OrgScopeOut


class ContractOut(BaseModel):
    id: int
    vendor_id: int
    type: str
    currency: str | None
    value: float | None
    retention_pct: float | None
    org_scope: OrgScopeOut


class CreateContractRequest(BaseModel):
    vendor_id: int
    type: str
    currency: str | None = None
    value: float | None = None
    retention_pct: float | None = None
    company_code: str | None = None
    plant: str | None = None
