from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.schedule_activity import ScheduleActivity
from domain.repositories.schedule_activity_repository import ScheduleActivityRepository
from infrastructure.persistence.orm_models import (
    ScheduleActivityModel,
    schedule_activity_predecessor_refs,
    schedule_activity_submittal_refs,
)


class SqlAlchemyScheduleActivityRepository(ScheduleActivityRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _predecessor_ids(self, activity_id: int) -> list[int]:
        return list(
            self._session.execute(
                select(schedule_activity_predecessor_refs.c.predecessor_id).where(
                    schedule_activity_predecessor_refs.c.schedule_activity_id == activity_id
                )
            )
            .scalars()
            .all()
        )

    def _successor_ids(self, activity_id: int) -> list[int]:
        """The reverse of the predecessor edge — never a second, independently
        stored list (ADR-008)."""
        return list(
            self._session.execute(
                select(schedule_activity_predecessor_refs.c.schedule_activity_id).where(
                    schedule_activity_predecessor_refs.c.predecessor_id == activity_id
                )
            )
            .scalars()
            .all()
        )

    def _linked_submittal_ids(self, activity_id: int) -> list[int]:
        return list(
            self._session.execute(
                select(schedule_activity_submittal_refs.c.submittal_id).where(
                    schedule_activity_submittal_refs.c.schedule_activity_id == activity_id
                )
            )
            .scalars()
            .all()
        )

    def _to_domain(self, row: ScheduleActivityModel) -> ScheduleActivity:
        return ScheduleActivity(
            id=row.id,
            project_id=row.project_id,
            activity_code=row.activity_code,
            type=row.type,
            wbs=row.wbs,
            predecessor_ids=self._predecessor_ids(row.id),
            successor_ids=self._successor_ids(row.id),
            linked_submittal_ids=self._linked_submittal_ids(row.id),
            delivery_milestone=row.delivery_milestone,
        )

    def get(self, schedule_activity_id: int) -> ScheduleActivity | None:
        row = self._session.get(ScheduleActivityModel, schedule_activity_id)
        return self._to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[ScheduleActivity]:
        rows = (
            self._session.execute(
                select(ScheduleActivityModel).where(ScheduleActivityModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def add(self, schedule_activity: ScheduleActivity) -> ScheduleActivity:
        row = ScheduleActivityModel(
            project_id=schedule_activity.project_id,
            activity_code=schedule_activity.activity_code,
            type=schedule_activity.type,
            wbs=schedule_activity.wbs,
            delivery_milestone=schedule_activity.delivery_milestone,
        )
        self._session.add(row)
        self._session.flush()
        for predecessor_id in schedule_activity.predecessor_ids:
            self._session.execute(
                schedule_activity_predecessor_refs.insert().values(
                    schedule_activity_id=row.id, predecessor_id=predecessor_id
                )
            )
        for submittal_id in schedule_activity.linked_submittal_ids:
            self._session.execute(
                schedule_activity_submittal_refs.insert().values(
                    schedule_activity_id=row.id, submittal_id=submittal_id
                )
            )
        self._session.flush()
        return self._to_domain(row)
