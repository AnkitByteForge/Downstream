from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities import RFI
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.state_machines import rfi_transitions
from domain.value_objects import BallInCourt


def make_rfi(status: str = "DRAFT", response: str | None = None) -> RFI:
    return RFI(
        id=1,
        project_id=1,
        number="214",
        display_number="RFI-214",
        subject="Duct routing conflict",
        ball_in_court=BallInCourt("assignee", None),
        status=status,
        response=response,
    )


def test_open_rfi_from_draft_sets_ball_in_court_to_assignee():
    rfi = make_rfi("DRAFT")
    opened = rfi_transitions.open_rfi(rfi, assignee_user_id=42)
    assert opened.status == "OPEN"
    assert opened.ball_in_court == BallInCourt("assignee", 42)


def test_open_rfi_from_non_draft_raises():
    rfi = make_rfi("OPEN")
    with pytest.raises(InvalidTransition):
        rfi_transitions.open_rfi(rfi, assignee_user_id=42)


def test_respond_to_rfi_sets_ball_in_court_to_manager():
    rfi = make_rfi("OPEN")
    responded = rfi_transitions.respond_to_rfi(rfi, "Reroute duct per SK-14.", manager_user_id=7)
    assert responded.status == "RESPONDED"
    assert responded.response == "Reroute duct per SK-14."
    assert responded.ball_in_court == BallInCourt("manager", 7)


def test_respond_to_rfi_rejects_empty_response():
    rfi = make_rfi("OPEN")
    with pytest.raises(DomainRuleViolation):
        rfi_transitions.respond_to_rfi(rfi, "   ", manager_user_id=7)


def test_close_rfi_from_open_requires_a_response():
    rfi = make_rfi("OPEN")
    with pytest.raises(DomainRuleViolation):
        rfi_transitions.close_rfi(rfi, datetime.now(timezone.utc))


def test_close_rfi_from_open_with_response_succeeds():
    rfi = make_rfi("OPEN")
    closed_at = datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)
    closed = rfi_transitions.close_rfi(rfi, closed_at, response_text="Reroute per SK-14.")
    assert closed.status == "CLOSED"
    assert closed.closed_at == closed_at
    assert closed.response == "Reroute per SK-14."


def test_close_rfi_from_responded_reuses_existing_response():
    rfi = make_rfi("RESPONDED", response="Already on file.")
    closed = rfi_transitions.close_rfi(rfi, datetime.now(timezone.utc))
    assert closed.status == "CLOSED"
    assert closed.response == "Already on file."


def test_cannot_transition_out_of_closed():
    rfi = make_rfi("CLOSED", response="done")
    with pytest.raises(InvalidTransition):
        rfi_transitions.open_rfi(rfi, assignee_user_id=1)
