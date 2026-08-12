from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ScheduleActivityOut(BaseModel):
    id: int
    project_id: int
    activity_code: str
    type: str
    wbs: str | None
    predecessor_ids: list[int]
    successor_ids: list[int]
    linked_submittal_ids: list[int]
    delivery_milestone: datetime | None
