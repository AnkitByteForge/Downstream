from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.rfi_use_cases import CloseRFI, GetRFI, ListRFIs, RespondToRFI
from domain.entities import RFI, WebhookSubscription
from domain.value_objects import BallInCourt

from .fakes import (
    FakeClock,
    FakeWebhookDispatcher,
    InMemoryRFIRepository,
    InMemoryWebhookDeliveryRepository,
    InMemoryWebhookSubscriptionRepository,
)


def _seed_rfi(repo: InMemoryRFIRepository, status: str = "OPEN") -> RFI:
    return repo.add(
        RFI(
            id=None,
            project_id=1,
            number="214",
            display_number="RFI-214",
            subject="Duct routing conflict",
            ball_in_court=BallInCourt("assignee", 42),
            status=status,
        )
    )


def _make_close_rfi(
    rfi_repo: InMemoryRFIRepository,
    clock: FakeClock | None = None,
    subscriptions: list[WebhookSubscription] | None = None,
    dispatcher: FakeWebhookDispatcher | None = None,
) -> tuple[CloseRFI, InMemoryWebhookDeliveryRepository, FakeWebhookDispatcher]:
    delivery_repo = InMemoryWebhookDeliveryRepository()
    dispatcher = dispatcher or FakeWebhookDispatcher()
    use_case = CloseRFI(
        rfi_repo,
        clock or FakeClock(),
        InMemoryWebhookSubscriptionRepository(subscriptions),
        delivery_repo,
        dispatcher,
    )
    return use_case, delivery_repo, dispatcher


def test_get_rfi_raises_not_found_for_unknown_id():
    with pytest.raises(NotFound):
        GetRFI(InMemoryRFIRepository()).execute(999)


def test_list_rfis_filters_by_project():
    repo = InMemoryRFIRepository()
    _seed_rfi(repo)
    use_case = ListRFIs(repo)
    assert len(use_case.execute(1)) == 1
    assert use_case.execute(2) == []


def test_respond_to_rfi_persists_the_transition():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    updated = RespondToRFI(repo).execute(rfi.id, "Reroute per SK-14.", manager_user_id=7)
    assert updated.status == "RESPONDED"
    assert repo.get(rfi.id).status == "RESPONDED"


def test_close_rfi_uses_injected_clock_for_closed_at():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    clock = FakeClock()
    use_case, _, _ = _make_close_rfi(repo, clock=clock)
    closed = use_case.execute(rfi.id, response_text="Reroute per SK-14.")
    assert closed.status == "CLOSED"
    assert closed.closed_at == clock.now()


def test_close_rfi_dispatches_to_matching_subscription_with_thin_payload():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    subscription = WebhookSubscription(
        id=1, project_id=1, resource_name="rfis", event_type="update", target_url="http://x", secret="s"
    )
    use_case, delivery_repo, dispatcher = _make_close_rfi(repo, subscriptions=[subscription])

    closed = use_case.execute(rfi.id, response_text="Reroute per SK-14.")

    assert len(dispatcher.calls) == 1
    dispatched_subscription, payload = dispatcher.calls[0]
    assert dispatched_subscription.target_url == "http://x"
    assert set(payload.keys()) == {
        "resource_name",
        "resource_id",
        "project_id",
        "event_type",
        "timestamp",
    }
    assert payload["resource_name"] == "rfis"
    assert payload["resource_id"] == closed.id
    assert payload["project_id"] == 1
    assert payload["event_type"] == "update"

    assert len(delivery_repo.rows) == 1
    assert delivery_repo.rows[0].status == "SENT"


def test_close_rfi_records_failed_delivery_without_raising():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    subscription = WebhookSubscription(
        id=1, project_id=1, resource_name="rfis", event_type="update", target_url="http://x", secret="s"
    )
    failing_dispatcher = FakeWebhookDispatcher(always_succeed=False)
    use_case, delivery_repo, _ = _make_close_rfi(
        repo, subscriptions=[subscription], dispatcher=failing_dispatcher
    )

    closed = use_case.execute(rfi.id, response_text="Reroute per SK-14.")

    assert closed.status == "CLOSED"  # the transition still succeeds
    assert delivery_repo.rows[0].status == "FAILED"


def test_close_rfi_ignores_subscriptions_for_other_resource_types():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    unrelated = WebhookSubscription(
        id=1, project_id=1, resource_name="submittals", event_type="update", target_url="http://x", secret="s"
    )
    use_case, delivery_repo, dispatcher = _make_close_rfi(repo, subscriptions=[unrelated])

    use_case.execute(rfi.id, response_text="Reroute per SK-14.")

    assert dispatcher.calls == []
    assert delivery_repo.rows == []
