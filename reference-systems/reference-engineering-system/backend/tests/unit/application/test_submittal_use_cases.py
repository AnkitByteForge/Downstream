from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.submittal_use_cases import GetSubmittal, RecordSubmittalDisposition
from domain.entities.submittal import Submittal, SubmittalReviewStatus, SubmittalRevision
from domain.entities.webhook import WebhookSubscription
from domain.value_objects import BallInCourt

from .fakes import (
    FakeClock,
    FakeWebhookDispatcher,
    InMemorySubmittalRepository,
    InMemorySubmittalReviewStatusRepository,
    InMemorySubmittalRevisionRepository,
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)

PENDING = SubmittalReviewStatus(
    id=1, project_id=1, code="PENDING", label="Pending", gates_procurement=False, is_terminal=False
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


def _make_use_case(subscriptions=None, dispatcher=None):
    submittal_repo = InMemorySubmittalRepository(
        [Submittal(id=1, project_id=1, number="118", spec_section_id=1)]
    )
    revision_repo = InMemorySubmittalRevisionRepository(
        [
            SubmittalRevision(
                id=1,
                submittal_id=1,
                rev_label="Rev 1",
                review_status_id=PENDING.id,
                ball_in_court=BallInCourt("submitter", None),
            )
        ]
    )
    review_status_repo = InMemorySubmittalReviewStatusRepository(
        [PENDING, NO_EXCEPTIONS_TAKEN, REVISE_AND_RESUBMIT]
    )
    delivery_repo = InMemoryWebhookDeliveryRepository()
    dispatcher = dispatcher or FakeWebhookDispatcher()
    use_case = RecordSubmittalDisposition(
        submittal_repo,
        revision_repo,
        review_status_repo,
        FakeClock(),
        InMemoryWebhookSubscriptionRepository(subscriptions),
        delivery_repo,
        dispatcher,
    )
    return use_case, revision_repo, delivery_repo, dispatcher


def test_get_submittal_raises_not_found_for_unknown_id():
    with pytest.raises(NotFound):
        GetSubmittal(InMemorySubmittalRepository()).execute(999)


def test_record_disposition_persists_the_new_status():
    use_case, revision_repo, _, _ = _make_use_case()
    updated = use_case.execute(1, "NO_EXCEPTIONS_TAKEN", disposed_by_user_id=9)
    assert updated.review_status_id == NO_EXCEPTIONS_TAKEN.id
    assert revision_repo.get(1).review_status_id == NO_EXCEPTIONS_TAKEN.id


def test_record_disposition_dispatches_webhook_with_thin_payload_on_gating_status():
    subscription = WebhookSubscription(
        id=1, project_id=1, resource_name="submittals", event_type="update", target_url="http://x", secret="s"
    )
    use_case, _, delivery_repo, dispatcher = _make_use_case(subscriptions=[subscription])

    use_case.execute(1, "NO_EXCEPTIONS_TAKEN", disposed_by_user_id=9)

    assert len(dispatcher.calls) == 1
    _, payload = dispatcher.calls[0]
    assert set(payload.keys()) == {"resource_name", "resource_id", "project_id", "event_type", "timestamp"}
    assert payload["resource_name"] == "submittals"
    assert payload["resource_id"] == 1
    assert delivery_repo.rows[0].status == "SENT"


def test_record_disposition_dispatches_webhook_on_blocking_status_too():
    """Every disposition change is webhook-worthy, not only ones that release
    procurement — matches CloseRFI's always-fire behavior."""
    subscription = WebhookSubscription(
        id=1, project_id=1, resource_name="submittals", event_type="update", target_url="http://x", secret="s"
    )
    use_case, _, delivery_repo, dispatcher = _make_use_case(subscriptions=[subscription])

    use_case.execute(1, "REVISE_AND_RESUBMIT", disposed_by_user_id=9)

    assert len(dispatcher.calls) == 1
    assert delivery_repo.rows[0].status == "SENT"


def test_record_disposition_on_unknown_revision_raises_not_found():
    use_case, _, _, _ = _make_use_case()
    with pytest.raises(NotFound):
        use_case.execute(999, "NO_EXCEPTIONS_TAKEN", disposed_by_user_id=9)
