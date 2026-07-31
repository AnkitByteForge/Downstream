from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.webhook import WebhookDelivery, WebhookSubscription


class WebhookSubscriptionRepository(ABC):
    @abstractmethod
    def add(self, subscription: WebhookSubscription) -> WebhookSubscription: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[WebhookSubscription]: ...

    @abstractmethod
    def list_matching(
        self, project_id: int, resource_name: str, event_type: str
    ) -> list[WebhookSubscription]: ...


class WebhookDeliveryRepository(ABC):
    @abstractmethod
    def add(self, delivery: WebhookDelivery) -> WebhookDelivery: ...

    @abstractmethod
    def list_by_project(self, project_id: int, limit: int) -> list[WebhookDelivery]: ...
