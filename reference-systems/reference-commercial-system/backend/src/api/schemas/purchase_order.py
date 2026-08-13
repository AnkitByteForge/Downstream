from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from api.schemas.org_scope import OrgScopeOut


class PurchaseOrderOut(BaseModel):
    id: int
    po_number: str | None
    vendor_id: int
    currency: str
    org_scope: OrgScopeOut
    contract_id: int | None
    payment_terms: str | None
    status: str
    acknowledged: bool
    acknowledged_at: datetime | None
    delivery_completed: bool
    final_invoice: bool
    changed_at: datetime | None


class CreatePurchaseOrderRequest(BaseModel):
    vendor_id: int
    currency: str
    po_number: str | None = None
    contract_id: int | None = None
    payment_terms: str | None = None
    company_code: str | None = None
    plant: str | None = None
    purchasing_org: str | None = None


class POLineOut(BaseModel):
    id: int
    po_id: int
    line_no: int
    description: str
    quantity: float
    uom: str
    unit_price: float
    value: float
    cost_code_id: int | None
    spec_section_refs: list[str]
    lifecycle_position: str


class CreatePOLineRequest(BaseModel):
    line_no: int
    description: str
    quantity: float
    uom: str
    unit_price: float
    value: float
    cost_code_id: int | None = None
    spec_section_refs: list[str] = []
    lifecycle_position: str = "draft"


class POScheduleLineOut(BaseModel):
    id: int
    po_line_id: int
    schedule_no: int
    quantity: float
    required_on_site_date: date | None
    promised_date: date | None
    linked_schedule_activity_ref: str | None
    delivery_status: str


class CreatePOScheduleLineRequest(BaseModel):
    schedule_no: int
    quantity: float
    required_on_site_date: date | None = None
    promised_date: date | None = None
    linked_schedule_activity_ref: str | None = None
    delivery_status: str = "SCHEDULED"
