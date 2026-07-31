from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import WebhookSubscription


class WebhookDispatcherPort(ABC):
    """Fires a thin webhook payload at a subscription's target_url. Never
    raises — a dispatch failure is a fact to record (WebhookDelivery status),
    not an exception that should roll back the transition that triggered it."""

    @abstractmethod
    def dispatch(self, subscription: WebhookSubscription, payload: dict) -> bool:
        """Returns True if delivered, False if it failed after retry."""
        ...
