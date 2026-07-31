from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebhookSubscription:
    """A registered target for this system's thin, Procore-realistic
    outbound webhooks (docs/04's Mock Engineering System spec). Not part of
    the Procore-shaped /rest/v1.0/ surface — this is this system's own
    admin/setup concern, the same way registering a webhook is a Procore
    Developer Portal action, not a Procore resource API call."""

    id: int | None
    project_id: int
    resource_name: str  # e.g. "rfis"
    event_type: str  # e.g. "update"
    target_url: str
    secret: str


@dataclass
class WebhookDelivery:
    """A record of one dispatch attempt — the append-only log the Activity
    Feed reads from, and what makes webhook dispatch inspectable rather than
    fire-and-forget-and-forgotten."""

    id: int | None
    project_id: int
    subscription_id: int
    resource_name: str
    resource_id: int
    event_type: str
    occurred_at: datetime
    status: str  # "SENT" | "FAILED"
    dispatched_at: datetime
