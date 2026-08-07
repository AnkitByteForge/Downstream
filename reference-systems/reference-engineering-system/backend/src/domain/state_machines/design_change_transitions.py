from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from domain.entities.design_change import DesignChange
from domain.exceptions import InvalidTransition

# Engineering-document lifecycle (ADR-007):
#   DRAFT        -> ISSUED
#   ISSUED       -> ACKNOWLEDGED | SUPERSEDED | VOID
#   ACKNOWLEDGED -> SUPERSEDED
#   SUPERSEDED / VOID are terminal (no forward transitions).
# VOID is only reachable from DRAFT or ISSUED; an acknowledged document that
# has already been accepted cannot be voided. SUPERSEDED records the later
# DesignChange that replaced this one via superseded_by_id.
_ALLOWED: dict[str, set[str]] = {
    "DRAFT": {"ISSUED", "VOID"},
    "ISSUED": {"ACKNOWLEDGED", "SUPERSEDED", "VOID"},
    "ACKNOWLEDGED": {"SUPERSEDED"},
    "SUPERSEDED": set(),
    "VOID": set(),
}


def _check(change: DesignChange, to_status: str) -> None:
    if to_status not in _ALLOWED.get(change.status, set()):
        raise InvalidTransition("DesignChange", change.status, to_status)


def issue_design_change(change: DesignChange, issued_at: datetime) -> DesignChange:
    _check(change, "ISSUED")
    return replace(change, status="ISSUED", issued_at=issued_at)


def acknowledge_design_change(change: DesignChange, acknowledged_at: datetime) -> DesignChange:
    _check(change, "ACKNOWLEDGED")
    return replace(change, status="ACKNOWLEDGED", acknowledged_at=acknowledged_at)


def supersede_design_change(change: DesignChange, superseded_by_id: int) -> DesignChange:
    _check(change, "SUPERSEDED")
    return replace(change, status="SUPERSEDED", superseded_by_id=superseded_by_id)


def void_design_change(
    change: DesignChange, voided_at: datetime | None = None
) -> DesignChange:
    _check(change, "VOID")
    return replace(change, status="VOID", voided_at=voided_at)
