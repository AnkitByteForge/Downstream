from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ScheduleActivityModel(Base):
    __tablename__ = "schedule_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    activity_code: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(16))
    wbs: Mapped[str | None] = mapped_column(String(60), nullable=True)
    delivery_milestone: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


schedule_activity_predecessor_refs = Table(
    "schedule_activity_predecessors",
    Base.metadata,
    Column("schedule_activity_id", ForeignKey("schedule_activities.id"), primary_key=True),
    Column("predecessor_id", ForeignKey("schedule_activities.id"), primary_key=True),
)

schedule_activity_submittal_refs = Table(
    "schedule_activity_submittals",
    Base.metadata,
    Column("schedule_activity_id", ForeignKey("schedule_activities.id"), primary_key=True),
    Column("submittal_id", ForeignKey("submittals.id"), primary_key=True),
)
