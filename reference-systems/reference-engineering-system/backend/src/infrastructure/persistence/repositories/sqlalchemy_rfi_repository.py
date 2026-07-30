from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import RFI
from domain.repositories import RFIRepository
from domain.value_objects import BallInCourt
from infrastructure.persistence.orm_models import RFIModel
from infrastructure.persistence.orm_models.rfi import (
    rfi_drawing_refs,
    rfi_location_refs,
    rfi_spec_section_refs,
)


class SqlAlchemyRFIRepository(RFIRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, row: RFIModel) -> RFI:
        drawing_version_ids = list(
            self._session.execute(
                select(rfi_drawing_refs.c.version_id).where(rfi_drawing_refs.c.rfi_id == row.id)
            )
            .scalars()
            .all()
        )
        spec_section_ids = list(
            self._session.execute(
                select(rfi_spec_section_refs.c.spec_section_id).where(
                    rfi_spec_section_refs.c.rfi_id == row.id
                )
            )
            .scalars()
            .all()
        )
        location_ids = list(
            self._session.execute(
                select(rfi_location_refs.c.location_id).where(rfi_location_refs.c.rfi_id == row.id)
            )
            .scalars()
            .all()
        )
        return RFI(
            id=row.id,
            project_id=row.project_id,
            number=row.number,
            display_number=row.display_number,
            subject=row.subject,
            question=row.question,
            response=row.response,
            status=row.status,
            ball_in_court=BallInCourt(row.ball_in_court_role, row.ball_in_court_user_id),
            cost_impact_flag=row.cost_impact_flag,
            cost_code=row.cost_code,
            discipline_code=row.discipline_code,
            spawned_change_id=row.spawned_change_id,
            raw_document_ref=row.raw_document_ref,
            drawing_version_ids=drawing_version_ids,
            spec_section_ids=spec_section_ids,
            location_ids=location_ids,
            closed_at=row.closed_at,
        )

    def get(self, rfi_id: int) -> RFI | None:
        row = self._session.get(RFIModel, rfi_id)
        return self._to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[RFI]:
        rows = (
            self._session.execute(select(RFIModel).where(RFIModel.project_id == project_id))
            .scalars()
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def add(self, rfi: RFI) -> RFI:
        row = RFIModel(
            project_id=rfi.project_id,
            number=rfi.number,
            display_number=rfi.display_number,
            subject=rfi.subject,
            question=rfi.question,
            response=rfi.response,
            status=rfi.status,
            ball_in_court_role=rfi.ball_in_court.party_role,
            ball_in_court_user_id=rfi.ball_in_court.user_id,
            cost_impact_flag=rfi.cost_impact_flag,
            cost_code=rfi.cost_code,
            discipline_code=rfi.discipline_code,
            spawned_change_id=rfi.spawned_change_id,
            raw_document_ref=rfi.raw_document_ref,
            closed_at=rfi.closed_at,
        )
        self._session.add(row)
        self._session.flush()
        for version_id in rfi.drawing_version_ids:
            self._session.execute(
                rfi_drawing_refs.insert().values(rfi_id=row.id, version_id=version_id)
            )
        for section_id in rfi.spec_section_ids:
            self._session.execute(
                rfi_spec_section_refs.insert().values(rfi_id=row.id, spec_section_id=section_id)
            )
        for location_id in rfi.location_ids:
            self._session.execute(
                rfi_location_refs.insert().values(rfi_id=row.id, location_id=location_id)
            )
        self._session.flush()
        return self._to_domain(row)

    def update(self, rfi: RFI) -> RFI:
        row = self._session.get(RFIModel, rfi.id)
        row.status = rfi.status
        row.response = rfi.response
        row.ball_in_court_role = rfi.ball_in_court.party_role
        row.ball_in_court_user_id = rfi.ball_in_court.user_id
        row.closed_at = rfi.closed_at
        self._session.flush()
        return self._to_domain(row)
