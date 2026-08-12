from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.schedule_activity import ScheduleActivity


class ScheduleActivityRepository(ABC):
    """Persistence port for ScheduleActivity (RES-5). Read-only surface — no
    `update`, nothing mutates a schedule activity through this system."""

    @abstractmethod
    def get(self, schedule_activity_id: int) -> ScheduleActivity | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[ScheduleActivity]: ...

    @abstractmethod
    def add(self, schedule_activity: ScheduleActivity) -> ScheduleActivity: ...
