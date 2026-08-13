from __future__ import annotations

from pydantic import BaseModel

from api.schemas.org_scope import OrgScopeOut


class CommitmentOut(BaseModel):
    id: int
    source_type: str
    cost_code_id: int
    po_id: int | None
    committed_amount: float
    relieved_amount: float
    open_amount: float
    currency: str
    status: str
    org_scope: OrgScopeOut


class CreateCommitmentRequest(BaseModel):
    source_type: str
    cost_code_id: int
    committed_amount: float
    currency: str
    po_id: int | None = None
    company_code: str | None = None
    plant: str | None = None


class RelieveCommitmentRequest(BaseModel):
    amount: float
