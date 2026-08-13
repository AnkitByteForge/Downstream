from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import DomainRuleViolation
from domain.value_objects import OrgScope

# 04_Downstream_Connector_Layer_Validation.md's cost_code_format field —
# "cost code" is five different concepts across the five real ERPs; the
# Graph Layer's key-matching needs to know which normalizer applies.
COST_CODE_FORMATS = (
    "CSI_MASTERFORMAT",
    "SAP_WBS",
    "ORACLE_PROJECT_TASK",
    "ERPNEXT_COST_CENTER",
    "CUSTOM",
)


@dataclass
class CostCode:
    """The Reference Commercial System.md §M item 9 — the normalization
    anchor and the literal join key to the Reference Engineering System's
    SpecSection, via `standard_ref` (a CSI MasterFormat number, e.g.
    "23 31 13"). `standard_ref` is a plain business key, never a foreign
    key — the two systems share no database (ADR-014)."""

    id: int | None
    native_code: str  # e.g. "23-100" — this system's own display code
    cost_code_format: str
    standard_ref: str | None = None  # e.g. "23 31 13" (CSI MasterFormat section)
    parent_id: int | None = None
    org_scope: OrgScope = OrgScope()
    budget_baseline: float | None = None
    budget_current: float | None = None
    committed: float | None = None
    actual: float | None = None
    etc: float | None = None  # estimate-to-complete
    eac: float | None = None  # estimate-at-completion

    def __post_init__(self) -> None:
        if self.cost_code_format not in COST_CODE_FORMATS:
            raise DomainRuleViolation(
                f"CostCode.cost_code_format must be one of {COST_CODE_FORMATS}, "
                f"got {self.cost_code_format!r}"
            )
