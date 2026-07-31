from __future__ import annotations

import json
import logging

import httpx

from application.ports import WebhookDispatcherPort
from domain.entities import WebhookSubscription
from infrastructure.webhooks.signing import sign_payload

logger = logging.getLogger(__name__)


class HttpWebhookDispatcher(WebhookDispatcherPort):
    """POSTs the thin payload to the subscription's target_url, HMAC-signed.
    One retry on a connection-level failure, then logged and dropped — no
    dead-letter queue, no backoff schedule (explicitly deferred past RES-2,
    per the approved plan; that's Synchronization Service territory in a
    much later Downstream milestone, not this system's job)."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout_seconds = timeout_seconds

    def dispatch(self, subscription: WebhookSubscription, payload: dict) -> bool:
        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "X-Signature": sign_payload(subscription.secret, body),
        }
        for attempt in range(2):
            try:
                response = httpx.post(
                    subscription.target_url,
                    content=body,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
                if response.status_code < 300:
                    return True
                logger.warning(
                    "Webhook delivery to %s returned %s", subscription.target_url, response.status_code
                )
                return False
            except httpx.RequestError as exc:
                if attempt == 1:
                    logger.warning("Webhook delivery to %s failed: %s", subscription.target_url, exc)
                    return False
        return False
