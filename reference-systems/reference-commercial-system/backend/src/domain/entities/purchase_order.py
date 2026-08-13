from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from domain.exceptions import DomainRuleViolation
from domain.value_objects import OrgScope

# PurchaseOrder header status — a normalized superset of Oracle Fusion's 15
# documented statuses and SAP's release-indicator/flag model, per The
# Reference Commercial System.md §C and its own Caveats ("the model should
# treat state names as a normalized superset, not a copy of any one
# vendor"). Flags below (acknowledged/delivery_completed/final_invoice)
# carry what SAP models as boolean indicators (ELIKZ etc.) rather than
# folding them into the status chain, matching SAP's own approach.
PO_STATUSES = (
    "DRAFT",
    "PENDING_APPROVAL",
    "OPEN",
    "PENDING_CHANGE_APPROVAL",
    "ON_HOLD",
    "CLOSED",
    "FINALLY_CLOSED",
    "CANCELED",
    "REJECTED",
    "WITHDRAWN",
)

# POLine fabrication/expediting sub-lifecycle (ADR-011) — the frozen
# `lifecycle_position` vocabulary from 05_Downstream_Reference_Execution_Trace.md
# / The Reference Commercial System.md §M item 3, lower-cased per the
# product-design documents' own casing (packages/envelope-schemas leaves
# this a free string precisely because the two frozen sources disagree on
# case; this system picks the lower-case form and is the literal source of
# truth a future connector-sap adapter must normalize against).
POLINE_LIFECYCLE_POSITIONS = ("draft", "issued", "in_fabrication", "shipped", "installed")

# POScheduleLine.delivery_status — a plain descriptive field in CS-1 (the
# full Delivery/GoodsReceipt entity and its own state machine are CS-3
# scope, per the approved plan's milestone table); validated as a closed
# set now so CS-3 does not have to migrate free-text data later.
DELIVERY_STATUSES = (
    "SCHEDULED",
    "CONFIRMED_ASN",
    "IN_TRANSIT",
    "PARTIALLY_DELIVERED",
    "DELIVERED",
)


@dataclass
class PurchaseOrder:
    id: int | None
    po_number: str | None  # SAP-style display number, e.g. "4500018823" —
    # nullable: docs/05's own trace states PO-4488's SAP number as "(not
    # stated in trace)"; left absent rather than invented, per the
    # standing "do not invent commercial relationships/data not grounded
    # in the frozen documents" instruction.
    vendor_id: int
    currency: str
    org_scope: OrgScope = OrgScope()
    contract_id: int | None = None
    payment_terms: str | None = None
    status: str = "DRAFT"
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    delivery_completed: bool = False
    final_invoice: bool = False
    changed_at: datetime | None = None  # drives the `changed_since` polling
    # filter (docs/04: SAP/Oracle's native event push is often absent;
    # `$filter` on a changed-since timestamp is the documented fallback).

    def __post_init__(self) -> None:
        if self.status not in PO_STATUSES:
            raise DomainRuleViolation(f"PurchaseOrder.status must be one of {PO_STATUSES}, got {self.status!r}")


@dataclass
class POLine:
    id: int | None
    po_id: int
    line_no: int
    description: str
    quantity: float
    uom: str
    unit_price: float
    value: float
    cost_code_id: int | None = None  # nullable: docs/05's PO-4488/PO-4512 are
    # reached only via structural/temporal graph dependency, never a direct
    # cost-code citation ("(inherited via structural dependency)" /
    # "(inherited via temporal dependency)") — no cost code is stated for
    # either in the frozen trace, so none is invented here.
    spec_section_refs: list[str] = field(default_factory=list)
    lifecycle_position: str = "draft"

    def __post_init__(self) -> None:
        if self.lifecycle_position not in POLINE_LIFECYCLE_POSITIONS:
            raise DomainRuleViolation(
                f"POLine.lifecycle_position must be one of {POLINE_LIFECYCLE_POSITIONS}, "
                f"got {self.lifecycle_position!r}"
            )


@dataclass
class POScheduleLine:
    id: int | None
    po_line_id: int
    schedule_no: int
    quantity: float
    required_on_site_date: date | None = None
    promised_date: date | None = None
    linked_schedule_activity_ref: str | None = None  # external business key
    # into the Reference Engineering System's ScheduleActivity.activity_code
    # (e.g. "3410") — never a foreign key across services (ADR-014).
    delivery_status: str = "SCHEDULED"

    def __post_init__(self) -> None:
        if self.delivery_status not in DELIVERY_STATUSES:
            raise DomainRuleViolation(
                f"POScheduleLine.delivery_status must be one of {DELIVERY_STATUSES}, "
                f"got {self.delivery_status!r}"
            )
