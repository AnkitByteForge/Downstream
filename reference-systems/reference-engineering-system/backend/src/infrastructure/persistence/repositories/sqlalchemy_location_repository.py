from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import Location
from domain.repositories import LocationRepository
from infrastructure.persistence.orm_models import LocationModel


def _to_domain(row: LocationModel) -> Location:
    return Location(
        id=row.id,
        project_id=row.project_id,
        parent_id=row.parent_id,
        tier_level=row.tier_level,
        name=row.name,
        type=row.type,
    )


class SqlAlchemyLocationRepository(LocationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, location_id: int) -> Location | None:
        row = self._session.get(LocationModel, location_id)
        return _to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[Location]:
        rows = (
            self._session.execute(
                select(LocationModel).where(LocationModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [_to_domain(r) for r in rows]

    def add(self, location: Location) -> Location:
        row = LocationModel(
            project_id=location.project_id,
            parent_id=location.parent_id,
            tier_level=location.tier_level,
            name=location.name,
            type=location.type,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)
