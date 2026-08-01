from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from domain.entities.submittal import SubmittalRevision, SubmittalReviewStatus
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.value_objects import BallInCourt


def submit_revision(
    revision: SubmittalRevision, reviewer_user_id: int, now: datetime
) -> SubmittalRevision:
    return replace(
        revision, ball_in_court=BallInCourt("reviewer", reviewer_user_id), submitted_at=now
    )


def record_disposition(
    revision: SubmittalRevision,
    current_status: SubmittalReviewStatus,
    new_status: SubmittalReviewStatus,
    disposed_by_user_id: int,
    now: datetime,
) -> SubmittalRevision:
    """A revision may receive a disposition once per non-terminal status
    (ADR-003's is_terminal flag, not a hardcoded status code) — once
    terminal, a new disposition requires a new revision, mirroring how a
    real approved/rejected submittal isn't silently re-reviewed in place.

    Ball-in-court after disposition: "closed" (nothing further to route)
    when the new status releases procurement; "submitter" (must revise and
    resubmit) when it doesn't — driven entirely by gates_procurement, never
    by matching a specific status code.
    """
    if current_status.is_terminal:
        raise InvalidTransition("SubmittalRevision", current_status.code, new_status.code)
    if current_status.id != revision.review_status_id:
        raise DomainRuleViolation(
            "current_status does not match the revision's own review_status_id"
        )
    next_role = "closed" if new_status.gates_procurement else "submitter"
    return replace(
        revision,
        review_status_id=new_status.id,
        ball_in_court=BallInCourt(next_role, None),
        disposed_by_user_id=disposed_by_user_id,
        disposition_at=now,
    )
