from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WebhookSubscriptionIn(BaseModel):
    resource_name: str
    event_type: str
    target_url: str
    secret: str


class WebhookSubscriptionOut(BaseModel):
    id: int
    project_id: int
    resource_name: str
    event_type: str
    target_url: str


class ActivityEntryOut(BaseModel):
    id: int
    project_id: int
    resource_name: str
    resource_id: int
    event_type: str
    occurred_at: datetime
    status: str
    dispatched_at: datetime
