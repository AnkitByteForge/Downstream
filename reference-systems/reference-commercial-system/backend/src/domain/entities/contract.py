from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import DomainRuleViolation
from domain.value_objects import OrgScope

# The Reference Commercial System.md §M item 5: blanket / scheduling
# agreement / subcontract — parent of POs/releases.
CONTRACT_TYPES = ("BLANKET", "SCHEDULING_AGREEMENT", "SUBCONTRACT")


@dataclass
class Contract:
    id: int | None
    vendor_id: int
    type: str
    currency: str | None = None
    value: float | None = None
    retention_pct: float | None = None
    org_scope: OrgScope = OrgScope()

    def __post_init__(self) -> None:
        if self.type not in CONTRACT_TYPES:
            raise DomainRuleViolation(f"Contract.type must be one of {CONTRACT_TYPES}, got {self.type!r}")
