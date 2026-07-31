from __future__ import annotations

from domain.entities import WebhookDelivery, WebhookSubscription
from domain.repositories import WebhookDeliveryRepository, WebhookSubscriptionRepository


class RegisterWebhookSubscription:
    def __init__(self, subscription_repo: WebhookSubscriptionRepository) -> None:
        self._subscription_repo = subscription_repo

    def execute(
        self, project_id: int, resource_name: str, event_type: str, target_url: str, secret: str
    ) -> WebhookSubscription:
        subscription = WebhookSubscription(
            id=None,
            project_id=project_id,
            resource_name=resource_name,
            event_type=event_type,
            target_url=target_url,
            secret=secret,
        )
        return self._subscription_repo.add(subscription)


class ListWebhookSubscriptions:
    def __init__(self, subscription_repo: WebhookSubscriptionRepository) -> None:
        self._subscription_repo = subscription_repo

    def execute(self, project_id: int) -> list[WebhookSubscription]:
        return self._subscription_repo.list_by_project(project_id)


class ListActivity:
    """Backs the Activity Feed — reads the same webhook-delivery log that
    dispatch itself writes to, rather than inventing a second event stream."""

    def __init__(self, delivery_repo: WebhookDeliveryRepository) -> None:
        self._delivery_repo = delivery_repo

    def execute(self, project_id: int, limit: int = 50) -> list[WebhookDelivery]:
        return self._delivery_repo.list_by_project(project_id, limit)
