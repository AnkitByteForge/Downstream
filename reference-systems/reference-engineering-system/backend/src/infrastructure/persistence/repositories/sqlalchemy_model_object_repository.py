from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.model_object import ModelObject
from domain.repositories.model_object_repository import ModelObjectRepository
from infrastructure.persistence.orm_models import ModelObjectModel


def _to_domain(row: ModelObjectModel) -> ModelObject:
    return ModelObject(
        id=row.id,
        project_id=row.project_id,
        discipline_code=row.discipline_code,
        appearance_profile=row.appearance_profile,
        location_id=row.location_id,
        resource_link_id=row.resource_link_id,
    )


class SqlAlchemyModelObjectRepository(ModelObjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, model_object_id: int) -> ModelObject | None:
        row = self._session.get(ModelObjectModel, model_object_id)
        return _to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[ModelObject]:
        rows = (
            self._session.execute(
                select(ModelObjectModel).where(ModelObjectModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [_to_domain(r) for r in rows]

    def add(self, model_object: ModelObject) -> ModelObject:
        row = ModelObjectModel(
            project_id=model_object.project_id,
            discipline_code=model_object.discipline_code,
            appearance_profile=model_object.appearance_profile,
            location_id=model_object.location_id,
            resource_link_id=model_object.resource_link_id,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)
