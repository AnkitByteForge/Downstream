from __future__ import annotations

from pydantic import BaseModel

from api.schemas.org_scope import OrgScopeOut


class CostCodeOut(BaseModel):
    id: int
    native_code: str
    cost_code_format: str
    standard_ref: str | None
    parent_id: int | None
    org_scope: OrgScopeOut
    budget_baseline: float | None
    budget_current: float | None
    committed: float | None
    actual: float | None
    etc: float | None
    eac: float | None


class CreateCostCodeRequest(BaseModel):
    native_code: str
    cost_code_format: str
    standard_ref: str | None = None
    parent_id: int | None = None
    company_code: str | None = None
    plant: str | None = None
    budget_baseline: float | None = None
    budget_current: float | None = None
    committed: float | None = None
    actual: float | None = None
    etc: float | None = None
    eac: float | None = None
