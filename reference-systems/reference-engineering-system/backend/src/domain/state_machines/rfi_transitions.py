from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from domain.entities.rfi import RFI
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.value_objects import BallInCourt

# Draft -> Open(BIC=assignee) -> Responded(BIC=manager) -> Closed
_ALLOWED: dict[str, set[str]] = {
    "DRAFT": {"OPEN"},
    "OPEN": {"RESPONDED", "CLOSED"},
    "RESPONDED": {"CLOSED"},
    "CLOSED": set(),
}


def _check(rfi: RFI, to_status: str) -> None:
    if to_status not in _ALLOWED.get(rfi.status, set()):
        raise InvalidTransition("RFI", rfi.status, to_status)


def open_rfi(rfi: RFI, assignee_user_id: int) -> RFI:
    _check(rfi, "OPEN")
    return replace(
        rfi, status="OPEN", ball_in_court=BallInCourt("assignee", assignee_user_id)
    )


def respond_to_rfi(rfi: RFI, response_text: str, manager_user_id: int) -> RFI:
    _check(rfi, "RESPONDED")
    if not response_text.strip():
        raise DomainRuleViolation("RFI cannot be responded to with empty response text")
    return replace(
        rfi,
        status="RESPONDED",
        response=response_text,
        ball_in_court=BallInCourt("manager", manager_user_id),
    )


def close_rfi(rfi: RFI, closed_at: datetime, response_text: str | None = None) -> RFI:
    """Closing directly from OPEN (with a response supplied at close time) is
    allowed because the Reference Execution Trace's own scenario closes
    RFI-214 in one step alongside its response — the formal RESPONDED
    intermediate is available but not mandatory."""
    _check(rfi, "CLOSED")
    response = response_text if response_text is not None else rfi.response
    if not response:
        raise DomainRuleViolation("RFI cannot be closed without a recorded response")
    return replace(rfi, status="CLOSED", response=response, closed_at=closed_at)
