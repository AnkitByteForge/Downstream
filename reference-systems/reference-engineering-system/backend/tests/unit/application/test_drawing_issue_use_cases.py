from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from application.exceptions import NotFound
from application.use_cases.drawing_use_cases import IssueDrawingVersion
from domain.entities import Drawing, DrawingVersion, WebhookSubscription
from domain.exceptions import InvalidTransition
from tests.unit.application.fakes import (
    FakeClock,
    FakeWebhookDispatcher,
    InMemoryDrawingRepository,
    InMemoryDrawingVersionRepository,
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)


def make_drawing(drawing_id: int, current_version_id: int | None = None) -> Drawing:
    return Drawing(
        id=drawing_id,
        project_id=1,
        sheet_number="E-1.1",
        title="Electrical Plan – Level 1",
        discipline_code="E",
        current_version_id=current_version_id,
    )


def make_version(version_id: int, drawing_id: int, status: str = "DRAFT") -> DrawingVersion:
    return DrawingVersion(
        id=version_id,
        drawing_id=drawing_id,
        revision_label="Rev 0",
        issuance_date=date(2026, 8, 7),
        status=status,
        discipline_code="E",
        superseded_by_id=None,
    )


def _use_case(drawing_repo, version_repo, dispatcher, deliveries, subscriptions):
    return IssueDrawingVersion(
        drawing_repo,
        version_repo,
        FakeClock(datetime(2026, 8, 10, 9, 0, 0, tzinfo=timezone.utc)),
        InMemoryWebhookSubscriptionRepository(subscriptions),
        deliveries,
        dispatcher,
    )


def _subscription(project_id: int = 1) -> WebhookSubscription:
    return WebhookSubscription(
        id=1, project_id=project_id, resource_name="documents", event_type="update",
        target_url="http://x", secret="s",
    )


def test_issue_issuance_stamps_date_supersedes_prior_and_repoints_drawing():
    drawing_repo = InMemoryDrawingRepository([make_drawing(1, current_version_id=1)])
    version_repo = InMemoryDrawingVersionRepository(
        [
            make_version(1, 1, status="ISSUED"),  # prior current
            make_version(2, 1, status="DRAFT"),   # the version being issued
        ]
    )
    dispatcher = FakeWebhookDispatcher()
    deliveries = InMemoryWebhookDeliveryRepository()
    use_case = _use_case(drawing_repo, version_repo, dispatcher, deliveries, [_subscription()])

    issued = use_case.execute(2)

    assert issued.status == "ISSUED"
    assert issued.issuance_date == date(2026, 8, 10)  # stamped at issuance

    prior = version_repo.get(1)
    assert prior.status == "SUPERSEDED"
    assert prior.superseded_by_id == 2

    assert drawing_repo.get(1).current_version_id == 2

    assert len(dispatcher.calls) == 1
    _, payload = dispatcher.calls[0]
    assert set(payload.keys()) == {"resource_name", "resource_id", "project_id", "event_type", "timestamp"}
    assert payload == {
        "resource_name": "documents",
        "resource_id": 2,  # VERSION id, not drawing id
        "project_id": 1,
        "event_type": "update",
        "timestamp": "2026-08-10T09:00:00+00:00",
    }
    assert len(deliveries.rows) == 1
    assert deliveries.rows[0].resource_id == 2
    assert deliveries.rows[0].status == "SENT"


def test_issue_with_no_prior_current_does_not_supersede_anything():
    drawing_repo = InMemoryDrawingRepository([make_drawing(1, current_version_id=None)])
    version_repo = InMemoryDrawingVersionRepository([make_version(5, 1, status="DRAFT")])
    dispatcher = FakeWebhookDispatcher()
    deliveries = InMemoryWebhookDeliveryRepository()
    use_case = _use_case(drawing_repo, version_repo, dispatcher, deliveries, [])

    issued = use_case.execute(5)

    assert issued.status == "ISSUED"
    assert drawing_repo.get(1).current_version_id == 5
    assert dispatcher.calls == []
    assert deliveries.rows == []


def test_issue_from_non_draft_raises_invalid_transition():
    drawing_repo = InMemoryDrawingRepository([make_drawing(1, current_version_id=None)])
    version_repo = InMemoryDrawingVersionRepository([make_version(3, 1, status="ISSUED")])
    use_case = _use_case(drawing_repo, version_repo, FakeWebhookDispatcher(), InMemoryWebhookDeliveryRepository(), [])
    with pytest.raises(InvalidTransition):
        use_case.execute(3)


def test_issue_unknown_version_raises_not_found():
    drawing_repo = InMemoryDrawingRepository([make_drawing(1, current_version_id=None)])
    version_repo = InMemoryDrawingVersionRepository([])
    use_case = _use_case(drawing_repo, version_repo, FakeWebhookDispatcher(), InMemoryWebhookDeliveryRepository(), [])
    with pytest.raises(NotFound):
        use_case.execute(99)