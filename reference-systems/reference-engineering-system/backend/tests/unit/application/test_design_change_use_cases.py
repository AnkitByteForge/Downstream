from __future__ import annotations

from datetime import datetime, timezone

import pytest

from application.exceptions import NotFound
from application.use_cases.design_change_use_cases import (
    AcknowledgeDesignChange,
    GetDesignChange,
    IssueDesignChange,
    ListDesignChanges,
    SupersedeDesignChange,
    VoidDesignChange,
)
from domain.entities.design_change import DesignChange
from domain.entities.webhook import WebhookSubscription
from domain.exceptions import InvalidTransition
from tests.unit.application.fakes import (
    FakeClock,
    FakeWebhookDispatcher,
    InMemoryDesignChangeRepository,
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)
from domain.value_objects import BallInCourt


def make_change(type_: str = "ASI", status: str = "DRAFT", change_id: int | None = None) -> DesignChange:
    return DesignChange(
        id=change_id,
        project_id=1,
        number="7",
        display_number="ASI-07",
        type=type_,
        status=status,
        change_reason="Larger RTU for Level 1",
        source_rfi_id=None,
        ball_in_court=BallInCourt("architect", None),
        affected_drawing_version_ids=[],
        affected_spec_section_ids=[],
        location_ids=[],
    )


def _subscription(project_id: int = 1) -> WebhookSubscription:
    return WebhookSubscription(
        id=1, project_id=project_id, resource_name="design_changes", event_type="update",
        target_url="http://x", secret="s",
    )


def _issue_use_case(repo, dispatcher, deliveries, subscriptions):
    return IssueDesignChange(
        repo,
        FakeClock(datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)),
        InMemoryWebhookSubscriptionRepository(subscriptions),
        deliveries,
        dispatcher,
    )


# --- List / Get ---------------------------------------------------------------

def test_list_design_changes_filters_by_project():
    repo = InMemoryDesignChangeRepository(
        [make_change(change_id=1, type_="ASI", status="DRAFT"),
         make_change(change_id=2, type_="CCD", status="ISSUED")]
    )
    listed = ListDesignChanges(repo).execute(1)
    assert len(listed) == 2
    assert ListDesignChanges(repo).execute(99) == []


def test_get_design_change_returns_or_raises():
    repo = InMemoryDesignChangeRepository([make_change(change_id=1, type_="BULLETIN", status="ISSUED")])
    found = GetDesignChange(repo).execute(1)
    assert found.display_number == "ASI-07"
    with pytest.raises(NotFound):
        GetDesignChange(repo).execute(99)


# --- Issue (webhook) ---------------------------------------------------------

def test_issue_design_change_transitions_and_dispatches_thin_webhook():
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, type_="ASI", status="DRAFT")])
    dispatcher = FakeWebhookDispatcher()
    deliveries = InMemoryWebhookDeliveryRepository()
    use_case = _issue_use_case(repo, dispatcher, deliveries, [_subscription()])

    issued = use_case.execute(7)

    assert issued.status == "ISSUED"
    assert issued.issued_at == datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)
    assert repo.get(7).status == "ISSUED"

    assert len(dispatcher.calls) == 1
    subscription, payload = dispatcher.calls[0]
    assert set(payload.keys()) == {"resource_name", "resource_id", "project_id", "event_type", "timestamp"}
    assert payload == {
        "resource_name": "design_changes",
        "resource_id": 7,
        "project_id": 1,
        "event_type": "update",
        "timestamp": "2026-08-07T12:00:00+00:00",
    }
    assert len(deliveries.rows) == 1
    assert deliveries.rows[0].status == "SENT"
    assert deliveries.rows[0].resource_name == "design_changes"


def test_issue_records_failed_delivery_without_rolling_back_transition():
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="DRAFT")])
    dispatcher = FakeWebhookDispatcher(always_succeed=False)
    deliveries = InMemoryWebhookDeliveryRepository()
    use_case = _issue_use_case(repo, dispatcher, deliveries, [_subscription()])

    issued = use_case.execute(7)

    assert issued.status == "ISSUED"  # transition still commits
    assert deliveries.rows[0].status == "FAILED"


def test_issue_from_non_draft_raises() -> None:
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="ISSUED")])
    use_case = _issue_use_case(repo, FakeWebhookDispatcher(), InMemoryWebhookDeliveryRepository(), [])
    with pytest.raises(InvalidTransition):
        use_case.execute(7)


# --- Acknowledge / Void / Supersede -------------------------------------------

def test_acknowledge_from_issued():
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="ISSUED")])
    acknowledged = AcknowledgeDesignChange(repo, FakeClock()).execute(7)
    assert acknowledged.status == "ACKNOWLEDGED"


def test_void_from_draft():
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="DRAFT")])
    voided = VoidDesignChange(repo, FakeClock()).execute(7)
    assert voided.status == "VOID"


def test_supersede_from_issued():
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="ISSUED")])
    superseded = SupersedeDesignChange(repo).execute(7, superseded_by_id=10)
    assert superseded.status == "SUPERSEDED"
    assert superseded.superseded_by_id == 10


def test_illegal_transition_raises_from_use_case() -> None:
    repo = InMemoryDesignChangeRepository([make_change(change_id=7, status="ACKNOWLEDGED")])
    with pytest.raises(InvalidTransition):
        VoidDesignChange(repo, FakeClock()).execute(7)
