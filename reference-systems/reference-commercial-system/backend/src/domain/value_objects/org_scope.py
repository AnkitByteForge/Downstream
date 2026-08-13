from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrgScope:
    """Generalizes SAP's Company Code/Plant/Purchasing Org and Oracle's
    Business Unit (04_Downstream_Connector_Layer_Validation.md; The
    Reference Commercial System.md §L). Embedded as plain columns on every
    scoped table (Vendor scope views, CostCode, Contract, Commitment,
    PurchaseOrder) rather than a separate joined table — matching the
    approved Commercial System Implementation Plan v1 §5.

    All fields optional: not every resource is scoped on every dimension
    (e.g. a global CostCode template may carry no plant)."""

    company_code: str | None = None
    plant: str | None = None
    purchasing_org: str | None = None
    business_unit: str | None = None
