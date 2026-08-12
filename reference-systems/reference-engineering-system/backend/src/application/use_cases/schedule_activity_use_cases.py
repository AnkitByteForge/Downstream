from __future__ import annotations

from application.exceptions import NotFound
from domain.entities.schedule_activity import ScheduleActivity
from domain.repositories.schedule_activity_repository import ScheduleActivityRepository


class ListScheduleActivities:
    def __init__(self, repo: ScheduleActivityRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int) -> list[ScheduleActivity]:
        return self._repo.list_by_project(project_id)


class GetScheduleActivity:
    def __init__(self, repo: ScheduleActivityRepository) -> None:
        self._repo = repo

    def execute(self, schedule_activity_id: int) -> ScheduleActivity:
        activity = self._repo.get(schedule_activity_id)
        if activity is None:
            raise NotFound("ScheduleActivity", schedule_activity_id)
        return activity
