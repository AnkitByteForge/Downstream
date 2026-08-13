from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import DomainRuleViolation
from domain.value_objects import OrgScope

# The Reference Commercial System.md §M item 4 (ADR-013: Commitment is
# first-class, not a derived PO attribute — committed cost changes before
# any invoice, per SAP's predictive commitment ledger 0E).
COMMITMENT_SOURCE_TYPES = ("PO", "SUBCONTRACT", "CHANGE_ORDER")
COMMITMENT_STATUSES = ("OPEN", "PARTIALLY_RELIEVED", "FULLY_RELIEVED", "CANCELLED")


@dataclass
class Commitment:
    id: int | None
    source_type: str
    cost_code_id: int
    committed_amount: float
    currency: str
    po_id: int | None = None
    relieved_amount: float = 0.0
    status: str = "OPEN"
    org_scope: OrgScope = OrgScope()

    def __post_init__(self) -> None:
        if self.source_type not in COMMITMENT_SOURCE_TYPES:
            raise DomainRuleViolation(
                f"Commitment.source_type must be one of {COMMITMENT_SOURCE_TYPES}, "
                f"got {self.source_type!r}"
            )
        if self.status not in COMMITMENT_STATUSES:
            raise DomainRuleViolation(
                f"Commitment.status must be one of {COMMITMENT_STATUSES}, got {self.status!r}"
            )

    @property
    def open_amount(self) -> float:
        return self.committed_amount - self.relieved_amount
