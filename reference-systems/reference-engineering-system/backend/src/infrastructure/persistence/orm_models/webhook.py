from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WebhookSubscriptionModel(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    resource_name: Mapped[str] = mapped_column(String(40))
    event_type: Mapped[str] = mapped_column(String(24))
    target_url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(200))


class WebhookDeliveryModel(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("webhook_subscriptions.id"))
    resource_name: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[int] = mapped_column()
    event_type: Mapped[str] = mapped_column(String(24))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
