from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.design_change import DesignChange
from domain.repositories.design_change_repository import DesignChangeRepository
from domain.value_objects import BallInCourt
from infrastructure.persistence.orm_models import (
    DesignChangeModel,
    design_change_drawing_version_refs,
    design_change_location_refs,
    design_change_spec_section_refs,
)


class SqlAlchemyDesignChangeRepository(DesignChangeRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _join_ids(session: Session, table, key_col: str, fk_col: str, key_value: int) -> list[int]:
        return list(
            session.execute(select(table.c[fk_col]).where(table.c[key_col] == key_value))
            .scalars()
            .all()
        )

    def _to_domain(self, row: DesignChangeModel) -> DesignChange:
        return DesignChange(
            id=row.id,
            project_id=row.project_id,
            number=row.number,
            display_number=row.display_number,
            type=row.type,
            status=row.status,
            change_reason=row.change_reason,
            discipline_code=row.discipline_code,
            source_rfi_id=row.source_rfi_id,
            ball_in_court=BallInCourt(row.ball_in_court_role, row.ball_in_court_user_id),
            affected_drawing_version_ids=self._join_ids(
                self._session,
                design_change_drawing_version_refs,
                "design_change_id",
                "drawing_version_id",
                row.id,
            ),
            affected_spec_section_ids=self._join_ids(
                self._session,
                design_change_spec_section_refs,
                "design_change_id",
                "spec_section_id",
                row.id,
            ),
            location_ids=self._join_ids(
                self._session,
                design_change_location_refs,
                "design_change_id",
                "location_id",
                row.id,
            ),
            superseded_by_id=row.superseded_by_id,
            issued_at=row.issued_at,
            acknowledged_at=row.acknowledged_at,
            voided_at=row.voided_at,
        )

    def get(self, design_change_id: int) -> DesignChange | None:
        row = self._session.get(DesignChangeModel, design_change_id)
        return self._to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[DesignChange]:
        rows = (
            self._session.execute(
                select(DesignChangeModel).where(DesignChangeModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def add(self, design_change: DesignChange) -> DesignChange:
        row = DesignChangeModel(
            project_id=design_change.project_id,
            number=design_change.number,
            display_number=design_change.display_number,
            type=design_change.type,
            status=design_change.status,
            change_reason=design_change.change_reason,
            discipline_code=design_change.discipline_code,
            source_rfi_id=design_change.source_rfi_id,
            ball_in_court_role=design_change.ball_in_court.party_role,
            ball_in_court_user_id=design_change.ball_in_court.user_id,
            superseded_by_id=design_change.superseded_by_id,
            issued_at=design_change.issued_at,
            acknowledged_at=design_change.acknowledged_at,
            voided_at=design_change.voided_at,
        )
        self._session.add(row)
        self._session.flush()
        self._replace_refs(row.id, design_change)
        self._session.flush()
        return self._to_domain(row)

    def update(self, design_change: DesignChange) -> DesignChange:
        row = self._session.get(DesignChangeModel, design_change.id)
        row.status = design_change.status
        row.change_reason = design_change.change_reason
        row.source_rfi_id = design_change.source_rfi_id
        row.ball_in_court_role = design_change.ball_in_court.party_role
        row.ball_in_court_user_id = design_change.ball_in_court.user_id
        row.superseded_by_id = design_change.superseded_by_id
        row.issued_at = design_change.issued_at
        row.acknowledged_at = design_change.acknowledged_at
        row.voided_at = design_change.voided_at
        self._replace_refs(row.id, design_change)
        self._session.flush()
        return self._to_domain(row)

    def _replace_refs(self, design_change_id: int, design_change: DesignChange) -> None:
        self._session.execute(
            design_change_drawing_version_refs.delete().where(
                design_change_drawing_version_refs.c.design_change_id == design_change_id
            )
        )
        for drawing_version_id in design_change.affected_drawing_version_ids:
            self._session.execute(
                design_change_drawing_version_refs.insert().values(
                    design_change_id=design_change_id, drawing_version_id=drawing_version_id
                )
            )

        self._session.execute(
            design_change_spec_section_refs.delete().where(
                design_change_spec_section_refs.c.design_change_id == design_change_id
            )
        )
        for spec_section_id in design_change.affected_spec_section_ids:
            self._session.execute(
                design_change_spec_section_refs.insert().values(
                    design_change_id=design_change_id, spec_section_id=spec_section_id
                )
            )

        self._session.execute(
            design_change_location_refs.delete().where(
                design_change_location_refs.c.design_change_id == design_change_id
            )
        )
        for location_id in design_change.location_ids:
            self._session.execute(
                design_change_location_refs.insert().values(
                    design_change_id=design_change_id, location_id=location_id
                )
            )