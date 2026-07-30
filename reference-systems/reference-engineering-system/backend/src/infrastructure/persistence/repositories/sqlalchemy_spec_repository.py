from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import SpecDivision, SpecSection
from domain.repositories import SpecDivisionRepository, SpecSectionRepository
from infrastructure.persistence.orm_models import SpecDivisionModel, SpecSectionModel


def _to_domain(row: SpecSectionModel) -> SpecSection:
    return SpecSection(
        id=row.id,
        project_id=row.project_id,
        division_number=row.division_number,
        number=row.number,
        title=row.title,
        substitution_policy=row.substitution_policy,
    )


class SqlAlchemySpecDivisionRepository(SpecDivisionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self) -> list[SpecDivision]:
        rows = self._session.execute(select(SpecDivisionModel)).scalars().all()
        return [SpecDivision(number=r.number, title=r.title) for r in rows]

    def add(self, division: SpecDivision) -> SpecDivision:
        row = SpecDivisionModel(number=division.number, title=division.title)
        self._session.merge(row)
        self._session.flush()
        return division


class SqlAlchemySpecSectionRepository(SpecSectionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, section_id: int) -> SpecSection | None:
        row = self._session.get(SpecSectionModel, section_id)
        return _to_domain(row) if row else None

    def get_by_number(self, project_id: int, number: str) -> SpecSection | None:
        row = self._session.execute(
            select(SpecSectionModel).where(
                SpecSectionModel.project_id == project_id, SpecSectionModel.number == number
            )
        ).scalar_one_or_none()
        return _to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[SpecSection]:
        rows = (
            self._session.execute(
                select(SpecSectionModel).where(SpecSectionModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [_to_domain(r) for r in rows]

    def add(self, section: SpecSection) -> SpecSection:
        row = SpecSectionModel(
            project_id=section.project_id,
            division_number=section.division_number,
            number=section.number,
            title=section.title,
            substitution_policy=section.substitution_policy,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)
