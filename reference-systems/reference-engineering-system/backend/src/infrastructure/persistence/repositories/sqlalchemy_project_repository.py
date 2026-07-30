from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import Discipline, Project
from domain.repositories import DisciplineRepository, ProjectRepository
from infrastructure.persistence.orm_models import DisciplineModel, ProjectModel


def _to_domain(row: ProjectModel) -> Project:
    return Project(id=row.id, name=row.name, spec_format=row.spec_format)


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: int) -> Project | None:
        row = self._session.get(ProjectModel, project_id)
        return _to_domain(row) if row else None

    def list(self) -> list[Project]:
        rows = self._session.execute(select(ProjectModel)).scalars().all()
        return [_to_domain(r) for r in rows]

    def add(self, project: Project) -> Project:
        row = ProjectModel(name=project.name, spec_format=project.spec_format)
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)


class SqlAlchemyDisciplineRepository(DisciplineRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, code: str) -> Discipline | None:
        row = self._session.get(DisciplineModel, code)
        return Discipline(code=row.code, name=row.name) if row else None

    def list(self) -> list[Discipline]:
        rows = self._session.execute(select(DisciplineModel)).scalars().all()
        return [Discipline(code=r.code, name=r.name) for r in rows]

    def add(self, discipline: Discipline) -> Discipline:
        row = DisciplineModel(code=discipline.code, name=discipline.name)
        self._session.merge(row)
        self._session.flush()
        return discipline
