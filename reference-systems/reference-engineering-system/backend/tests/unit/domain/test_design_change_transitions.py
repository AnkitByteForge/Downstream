from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities import DesignChange
from domain.exceptions import DomainError, InvalidTransition
from domain.state_machines import design_change_transitions
from domain.value_objects import BallInCourt


def make_change(type_: str = "ASI", status: str = "DRAFT") -> DesignChange:
    return DesignChange(
        id=1,
        project_id=1,
        number="7",
        display_number="ASI-07",
        type=type_,
        status=status,
        ball_in_court=BallInCourt("architect", None),
    )


def _ts() -> datetime:
    return datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)


# --- Construction invariants ------------------------------------------------

def test_all_design_change_types_are_valid():
    for type_ in ("ASI", "CCD", "BULLETIN"):
        assert make_change(type_=type_).type == type_


def test_invalid_type_raises():
    with pytest.raises(DomainError):
        make_change(type_="PCO")


def test_invalid_status_raises():
    with pytest.raises(DomainError):
        make_change(status="PRICED")


def test_source_rfi_is_nullable():
    assert make_change().source_rfi_id is None


# --- DRAFT -> ISSUED ----------------------------------------------------------

def test_issue_from_draft_sets_status_and_issued_at():
    change = make_change(status="DRAFT")
    issued = design_change_transitions.issue_design_change(change, _ts())
    assert issued.status == "ISSUED"
    assert issued.issued_at == _ts()


def test_issue_from_non_draft_raises():
    with pytest.raises(InvalidTransition):
        design_change_transitions.issue_design_change(make_change(status="ISSUED"), _ts())


# --- ISSUED -> ACKNOWLEDGED ---------------------------------------------------

def test_acknowledge_from_issued():
    change = make_change(status="ISSUED")
    acknowledged = design_change_transitions.acknowledge_design_change(change, _ts())
    assert acknowledged.status == "ACKNOWLEDGED"
    assert acknowledged.acknowledged_at == _ts()


def test_acknowledge_from_draft_raises():
    with pytest.raises(InvalidTransition):
        design_change_transitions.acknowledge_design_change(make_change(status="DRAFT"), _ts())


# --- VOID (DRAFT or ISSUED) ---------------------------------------------------

def test_void_from_draft():
    voided = design_change_transitions.void_design_change(make_change(status="DRAFT"), _ts())
    assert voided.status == "VOID"
    assert voided.voided_at == _ts()


def test_void_from_issued():
    voided = design_change_transitions.void_design_change(make_change(status="ISSUED"), _ts())
    assert voided.status == "VOID"


def test_void_from_acknowledged_raises():
    with pytest.raises(InvalidTransition):
        design_change_transitions.void_design_change(make_change(status="ACKNOWLEDGED"), _ts())


# --- SUPERSEDED (ISSUED or ACKNOWLEDGED) ---------------------------------------

def test_supersede_from_issued():
    change = make_change(status="ISSUED")
    superseded = design_change_transitions.supersede_design_change(change, superseded_by_id=99)
    assert superseded.status == "SUPERSEDED"
    assert superseded.superseded_by_id == 99


def test_supersede_from_acknowledged():
    change = make_change(status="ACKNOWLEDGED")
    superseded = design_change_transitions.supersede_design_change(change, superseded_by_id=99)
    assert superseded.status == "SUPERSEDED"


def test_supersede_from_draft_raises():
    with pytest.raises(InvalidTransition):
        design_change_transitions.supersede_design_change(make_change(status="DRAFT"), superseded_by_id=99)


# --- Terminal-state dead ends --------------------------------------------------

def test_terminal_states_have_no_forward_transitions():
    voided = make_change(status="VOID")
    with pytest.raises(InvalidTransition):
        design_change_transitions.issue_design_change(voided, _ts())

    superseded = make_change(status="SUPERSEDED")
    with pytest.raises(InvalidTransition):
        design_change_transitions.acknowledge_design_change(superseded, _ts())


def test_transition_functions_are_pure_and_do_not_mutate_input():
    change = make_change(status="DRAFT")
    design_change_transitions.issue_design_change(change, _ts())
    assert change.status == "DRAFT"  # original untouched
    assert change.issued_at is None
