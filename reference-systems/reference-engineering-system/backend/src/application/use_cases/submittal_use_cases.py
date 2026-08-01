from __future__ import annotations

from application.exceptions import NotFound
from application.ports import ClockPort, WebhookDispatcherPort
from application.webhook_payloads import build_thin_payload
from domain.entities.submittal import Submittal, SubmittalRevision
from domain.entities.webhook import WebhookDelivery
from domain.repositories.submittal_repository import (
    SubmittalRepository,
    SubmittalReviewStatusRepository,
    SubmittalRevisionRepository,
)
from domain.repositories.webhook_repository import (
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)
from domain.state_machines import submittal_transitions


class ListSubmittals:
    def __init__(self, repo: SubmittalRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int) -> list[Submittal]:
        return self._repo.list_by_project(project_id)


class GetSubmittal:
    def __init__(self, repo: SubmittalRepository) -> None:
        self._repo = repo

    def execute(self, submittal_id: int) -> Submittal:
        submittal = self._repo.get(submittal_id)
        if submittal is None:
            raise NotFound("Submittal", submittal_id)
        return submittal


class ListSubmittalRevisions:
    def __init__(self, repo: SubmittalRevisionRepository) -> None:
        self._repo = repo

    def execute(self, submittal_id: int) -> list[SubmittalRevision]:
        revisions = self._repo.list_by_submittal(submittal_id)
        return sorted(revisions, key=lambda r: r.id or 0)


class GetSubmittalRevision:
    def __init__(self, repo: SubmittalRevisionRepository) -> None:
        self._repo = repo

    def execute(self, revision_id: int) -> SubmittalRevision:
        revision = self._repo.get(revision_id)
        if revision is None:
            raise NotFound("SubmittalRevision", revision_id)
        return revision


class RecordSubmittalDisposition:
    """Fires the same webhook-worthy pattern CloseRFI established: on any
    disposition change, dispatch the thin payload to every subscription
    registered for (project, "submittals", "update"), and record one
    WebhookDelivery per attempt regardless of outcome."""

    def __init__(
        self,
        submittal_repo: SubmittalRepository,
        revision_repo: SubmittalRevisionRepository,
        review_status_repo: SubmittalReviewStatusRepository,
        clock: ClockPort,
        webhook_subscription_repo: WebhookSubscriptionRepository,
        webhook_delivery_repo: WebhookDeliveryRepository,
        webhook_dispatcher: WebhookDispatcherPort,
    ) -> None:
        self._submittal_repo = submittal_repo
        self._revision_repo = revision_repo
        self._review_status_repo = review_status_repo
        self._clock = clock
        self._webhook_subscription_repo = webhook_subscription_repo
        self._webhook_delivery_repo = webhook_delivery_repo
        self._webhook_dispatcher = webhook_dispatcher

    def execute(
        self, revision_id: int, new_status_code: str, disposed_by_user_id: int
    ) -> SubmittalRevision:
        revision = self._revision_repo.get(revision_id)
        if revision is None:
            raise NotFound("SubmittalRevision", revision_id)
        submittal = self._submittal_repo.get(revision.submittal_id)
        if submittal is None:
            raise NotFound("Submittal", revision.submittal_id)
        current_status = self._review_status_repo.get(revision.review_status_id)
        if current_status is None:
            raise NotFound("SubmittalReviewStatus", revision.review_status_id)
        new_status = self._review_status_repo.get_by_code(submittal.project_id, new_status_code)
        if new_status is None:
            raise NotFound("SubmittalReviewStatus", new_status_code)

        updated = submittal_transitions.record_disposition(
            revision, current_status, new_status, disposed_by_user_id, self._clock.now()
        )
        saved = self._revision_repo.update(updated)
        self._dispatch_webhooks(submittal, saved)
        return saved

    def _dispatch_webhooks(self, submittal: Submittal, revision: SubmittalRevision) -> None:
        occurred_at = revision.disposition_at or self._clock.now()
        subscriptions = self._webhook_subscription_repo.list_matching(
            submittal.project_id, "submittals", "update"
        )
        for subscription in subscriptions:
            payload = build_thin_payload(
                "submittals", submittal.id, submittal.project_id, "update", occurred_at
            )
            delivered = self._webhook_dispatcher.dispatch(subscription, payload)
            self._webhook_delivery_repo.add(
                WebhookDelivery(
                    id=None,
                    project_id=submittal.project_id,
                    subscription_id=subscription.id,
                    resource_name="submittals",
                    resource_id=submittal.id,
                    event_type="update",
                    occurred_at=occurred_at,
                    status="SENT" if delivered else "FAILED",
                    dispatched_at=self._clock.now(),
                )
            )
