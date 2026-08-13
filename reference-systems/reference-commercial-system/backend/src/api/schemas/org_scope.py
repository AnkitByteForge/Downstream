from __future__ import annotations

from pydantic import BaseModel


class OrgScopeOut(BaseModel):
    company_code: str | None
    plant: str | None
    purchasing_org: str | None
    business_unit: str | None
