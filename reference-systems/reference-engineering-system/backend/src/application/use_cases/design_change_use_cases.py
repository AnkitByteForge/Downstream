from __future__ import annotations

from application.exceptions import NotFound
from application.ports import ClockPort, WebhookDispatcherPort
from application.webhook_payloads import build_thin_payload
from domain.entities.design_change import DesignChange
from domain.entities.webhook import WebhookDelivery
from domain.repositories.design_change_repository import DesignChangeRepository
from domain.repositories.webhook_repository import (
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)
from domain.state_machines import design_change_transitions


class ListDesignChanges:
    def __init__(self, repo: DesignChangeRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int) -> list[DesignChange]:
        return self._repo.list_by_project(project_id)


class GetDesignChange:
    def __init__(self, repo: DesignChangeRepository) -> None:
        self._repo = repo

    def execute(self, design_change_id: int) -> DesignChange:
        design_change = self._repo.get(design_change_id)
        if design_change is None:
            raise NotFound("DesignChange", design_change_id)
        return design_change


class IssueDesignChange:
    """The webhook-worthy lifecycle step: DRAFT -> ISSUED. Only this step
    emits a thin webhook (resource_name="design_changes", event_type="update")
    — acknowledge/void/supersede intentionally emit nothing (RES-4 approved
    decision). Mirrors the CloseRFI/RecordSubmittalDisposition dispatch and
    delivery-recording pattern exactly."""

    def __init__(
        self,
        repo: DesignChangeRepository,
        clock: ClockPort,
        webhook_subscription_repo: WebhookSubscriptionRepository,
        webhook_delivery_repo: WebhookDeliveryRepository,
        webhook_dispatcher: WebhookDispatcherPort,
    ) -> None:
        self._repo = repo
        self._clock = clock
        self._webhook_subscription_repo = webhook_subscription_repo
        self._webhook_delivery_repo = webhook_delivery_repo
        self._webhook_dispatcher = webhook_dispatcher

    def execute(self, design_change_id: int) -> DesignChange:
        change = self._repo.get(design_change_id)
        if change is None:
            raise NotFound("DesignChange", design_change_id)
        issued_at = self._clock.now()
        updated = design_change_transitions.issue_design_change(change, issued_at)
        saved = self._repo.update(updated)
        self._dispatch_webhooks(saved, issued_at)
        return saved

    def _dispatch_webhooks(self, change: DesignChange, issued_at) -> None:
        subscriptions = self._webhook_subscription_repo.list_matching(
            change.project_id, "design_changes", "update"
        )
        for subscription in subscriptions:
            payload = build_thin_payload(
                "design_changes", change.id, change.project_id, "update", issued_at
            )
            delivered = self._webhook_dispatcher.dispatch(subscription, payload)
            self._webhook_delivery_repo.add(
                WebhookDelivery(
                    id=None,
                    project_id=change.project_id,
                    subscription_id=subscription.id,
                    resource_name="design_changes",
                    resource_id=change.id,
                    event_type="update",
                    occurred_at=issued_at,
                    status="SENT" if delivered else "FAILED",
                    dispatched_at=self._clock.now(),
                )
            )


class AcknowledgeDesignChange:
    def __init__(self, repo: DesignChangeRepository, clock: ClockPort) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, design_change_id: int) -> DesignChange:
        change = self._repo.get(design_change_id)
        if change is None:
            raise NotFound("DesignChange", design_change_id)
        updated = design_change_transitions.acknowledge_design_change(
            change, self._clock.now()
        )
        return self._repo.update(updated)


class VoidDesignChange:
    def __init__(self, repo: DesignChangeRepository, clock: ClockPort) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, design_change_id: int) -> DesignChange:
        change = self._repo.get(design_change_id)
        if change is None:
            raise NotFound("DesignChange", design_change_id)
        updated = design_change_transitions.void_design_change(change, self._clock.now())
        return self._repo.update(updated)


class SupersedeDesignChange:
    """Marks an ISSUED/ACKNOWLEDGED DesignChange as superseded by a later one.
    No webhook — not a first-class engineering event on its own. No create
    endpoint exists in RES-4, so this use case exists to exercise the domain
    transition and for any future create/supersede path to reuse."""

    def __init__(self, repo: DesignChangeRepository) -> None:
        self._repo = repo

    def execute(self, design_change_id: int, superseded_by_id: int) -> DesignChange:
        change = self._repo.get(design_change_id)
        if change is None:
            raise NotFound("DesignChange", design_change_id)
        updated = design_change_transitions.supersede_design_change(
            change, superseded_by_id
        )
        return self._repo.update(updated)
