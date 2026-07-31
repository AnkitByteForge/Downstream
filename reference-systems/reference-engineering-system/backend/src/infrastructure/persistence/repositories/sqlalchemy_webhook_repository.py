from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import WebhookDelivery, WebhookSubscription
from domain.repositories import WebhookDeliveryRepository, WebhookSubscriptionRepository
from infrastructure.persistence.orm_models import WebhookDeliveryModel, WebhookSubscriptionModel


def _subscription_to_domain(row: WebhookSubscriptionModel) -> WebhookSubscription:
    return WebhookSubscription(
        id=row.id,
        project_id=row.project_id,
        resource_name=row.resource_name,
        event_type=row.event_type,
        target_url=row.target_url,
        secret=row.secret,
    )


def _delivery_to_domain(row: WebhookDeliveryModel) -> WebhookDelivery:
    return WebhookDelivery(
        id=row.id,
        project_id=row.project_id,
        subscription_id=row.subscription_id,
        resource_name=row.resource_name,
        resource_id=row.resource_id,
        event_type=row.event_type,
        occurred_at=row.occurred_at,
        status=row.status,
        dispatched_at=row.dispatched_at,
    )


class SqlAlchemyWebhookSubscriptionRepository(WebhookSubscriptionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, subscription: WebhookSubscription) -> WebhookSubscription:
        row = WebhookSubscriptionModel(
            project_id=subscription.project_id,
            resource_name=subscription.resource_name,
            event_type=subscription.event_type,
            target_url=subscription.target_url,
            secret=subscription.secret,
        )
        self._session.add(row)
        self._session.flush()
        return _subscription_to_domain(row)

    def list_by_project(self, project_id: int) -> list[WebhookSubscription]:
        rows = (
            self._session.execute(
                select(WebhookSubscriptionModel).where(
                    WebhookSubscriptionModel.project_id == project_id
                )
            )
            .scalars()
            .all()
        )
        return [_subscription_to_domain(r) for r in rows]

    def list_matching(
        self, project_id: int, resource_name: str, event_type: str
    ) -> list[WebhookSubscription]:
        rows = (
            self._session.execute(
                select(WebhookSubscriptionModel).where(
                    WebhookSubscriptionModel.project_id == project_id,
                    WebhookSubscriptionModel.resource_name == resource_name,
                    WebhookSubscriptionModel.event_type == event_type,
                )
            )
            .scalars()
            .all()
        )
        return [_subscription_to_domain(r) for r in rows]


class SqlAlchemyWebhookDeliveryRepository(WebhookDeliveryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, delivery: WebhookDelivery) -> WebhookDelivery:
        row = WebhookDeliveryModel(
            project_id=delivery.project_id,
            subscription_id=delivery.subscription_id,
            resource_name=delivery.resource_name,
            resource_id=delivery.resource_id,
            event_type=delivery.event_type,
            occurred_at=delivery.occurred_at,
            status=delivery.status,
            dispatched_at=delivery.dispatched_at,
        )
        self._session.add(row)
        self._session.flush()
        return _delivery_to_domain(row)

    def list_by_project(self, project_id: int, limit: int) -> list[WebhookDelivery]:
        rows = (
            self._session.execute(
                select(WebhookDeliveryModel)
                .where(WebhookDeliveryModel.project_id == project_id)
                .order_by(WebhookDeliveryModel.dispatched_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [_delivery_to_domain(r) for r in rows]
