from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities.submittal import SubmittalReviewStatus, SubmittalRevision
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.state_machines import submittal_transitions
from domain.value_objects import BallInCourt

PENDING = SubmittalReviewStatus(
    id=1, project_id=1, code="PENDING", label="Pending", gates_procurement=False, is_terminal=False
)
SUBMITTED = SubmittalReviewStatus(
    id=4, project_id=1, code="SUBMITTED", label="Submitted", gates_procurement=False, is_terminal=False
)
NO_EXCEPTIONS_TAKEN = SubmittalReviewStatus(
    id=2,
    project_id=1,
    code="NO_EXCEPTIONS_TAKEN",
    label="No Exceptions Taken",
    gates_procurement=True,
    is_terminal=True,
)
REVISE_AND_RESUBMIT = SubmittalReviewStatus(
    id=3,
    project_id=1,
    code="REVISE_AND_RESUBMIT",
    label="Revise and Resubmit",
    gates_procurement=False,
    is_terminal=True,
)


def make_revision(review_status_id: int = PENDING.id) -> SubmittalRevision:
    return SubmittalRevision(
        id=1,
        submittal_id=1,
        rev_label="Rev 0",
        review_status_id=review_status_id,
        ball_in_court=BallInCourt("submitter", None),
    )


def test_submit_revision_sets_ball_in_court_and_timestamp():
    revision = make_revision()
    now = datetime(2026, 6, 5, tzinfo=timezone.utc)
    submitted = submittal_transitions.submit_revision(revision, reviewer_user_id=7, now=now)
    assert submitted.ball_in_court == BallInCourt("reviewer", 7)
    assert submitted.submitted_at == now


def test_record_disposition_releasing_procurement_sets_ball_in_court_closed():
    revision = make_revision()
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    disposed = submittal_transitions.record_disposition(
        revision, PENDING, NO_EXCEPTIONS_TAKEN, disposed_by_user_id=9, now=now
    )
    assert disposed.review_status_id == NO_EXCEPTIONS_TAKEN.id
    assert disposed.ball_in_court == BallInCourt("closed", None)
    assert disposed.disposed_by_user_id == 9
    assert disposed.disposition_at == now


def test_record_disposition_blocking_procurement_sets_ball_in_court_submitter():
    revision = make_revision()
    disposed = submittal_transitions.record_disposition(
        revision, PENDING, REVISE_AND_RESUBMIT, disposed_by_user_id=9, now=datetime.now(timezone.utc)
    )
    assert disposed.ball_in_court == BallInCourt("submitter", None)


def test_record_disposition_on_already_terminal_status_raises():
    revision = make_revision(review_status_id=NO_EXCEPTIONS_TAKEN.id)
    with pytest.raises(InvalidTransition):
        submittal_transitions.record_disposition(
            revision,
            NO_EXCEPTIONS_TAKEN,
            REVISE_AND_RESUBMIT,
            disposed_by_user_id=9,
            now=datetime.now(timezone.utc),
        )


def test_record_disposition_rejects_mismatched_current_status():
    """SUBMITTED is deliberately non-terminal here, so this test isolates the
    mismatch check from the terminal check above it — the revision's actual
    status is PENDING, not SUBMITTED."""
    revision = make_revision(review_status_id=PENDING.id)
    with pytest.raises(DomainRuleViolation):
        submittal_transitions.record_disposition(
            revision,
            SUBMITTED,
            REVISE_AND_RESUBMIT,
            disposed_by_user_id=9,
            now=datetime.now(timezone.utc),
        )
