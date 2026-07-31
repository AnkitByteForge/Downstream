from __future__ import annotations

from application.exceptions import NotFound
from application.ports import ClockPort, WebhookDispatcherPort
from application.webhook_payloads import build_thin_payload
from domain.entities import RFI, WebhookDelivery
from domain.repositories import RFIRepository, WebhookDeliveryRepository, WebhookSubscriptionRepository
from domain.state_machines import rfi_transitions


class ListRFIs:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, project_id: int) -> list[RFI]:
        return self._rfi_repo.list_by_project(project_id)


class GetRFI:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, rfi_id: int) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        return rfi


class RespondToRFI:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, rfi_id: int, response_text: str, manager_user_id: int) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        updated = rfi_transitions.respond_to_rfi(rfi, response_text, manager_user_id)
        return self._rfi_repo.update(updated)


class CloseRFI:
    """Fires the webhook-worthy transition the whole Reference Execution Trace
    starts from (Phase 0): closing an RFI dispatches the thin, five-field
    webhook payload to every subscription registered for (project, "rfis",
    "update"), and records one WebhookDelivery per attempt regardless of
    outcome — a dispatch failure never rolls back the transition itself
    (docs/03: synchronization/notification failures must be visible, never
    silently swallowed, but also never allowed to corrupt domain state).
    """

    def __init__(
        self,
        rfi_repo: RFIRepository,
        clock: ClockPort,
        webhook_subscription_repo: WebhookSubscriptionRepository,
        webhook_delivery_repo: WebhookDeliveryRepository,
        webhook_dispatcher: WebhookDispatcherPort,
    ) -> None:
        self._rfi_repo = rfi_repo
        self._clock = clock
        self._webhook_subscription_repo = webhook_subscription_repo
        self._webhook_delivery_repo = webhook_delivery_repo
        self._webhook_dispatcher = webhook_dispatcher

    def execute(self, rfi_id: int, response_text: str | None = None) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        updated = rfi_transitions.close_rfi(rfi, self._clock.now(), response_text)
        saved = self._rfi_repo.update(updated)
        self._dispatch_webhooks(saved)
        return saved

    def _dispatch_webhooks(self, rfi: RFI) -> None:
        occurred_at = rfi.closed_at or self._clock.now()
        subscriptions = self._webhook_subscription_repo.list_matching(
            rfi.project_id, "rfis", "update"
        )
        for subscription in subscriptions:
            payload = build_thin_payload("rfis", rfi.id, rfi.project_id, "update", occurred_at)
            delivered = self._webhook_dispatcher.dispatch(subscription, payload)
            self._webhook_delivery_repo.add(
                WebhookDelivery(
                    id=None,
                    project_id=rfi.project_id,
                    subscription_id=subscription.id,
                    resource_name="rfis",
                    resource_id=rfi.id,
                    event_type="update",
                    occurred_at=occurred_at,
                    status="SENT" if delivered else "FAILED",
                    dispatched_at=self._clock.now(),
                )
            )
