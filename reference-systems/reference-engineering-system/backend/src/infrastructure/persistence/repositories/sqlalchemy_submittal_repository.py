from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.submittal import (
    Submittal,
    SubmittalPackage,
    SubmittalRequirement,
    SubmittalReviewStatus,
    SubmittalRevision,
)
from domain.repositories.submittal_repository import (
    SubmittalPackageRepository,
    SubmittalRepository,
    SubmittalRequirementRepository,
    SubmittalReviewStatusRepository,
    SubmittalRevisionRepository,
)
from domain.value_objects import BallInCourt
from infrastructure.persistence.orm_models import (
    SubmittalModel,
    SubmittalPackageModel,
    SubmittalRequirementModel,
    SubmittalReviewStatusModel,
    SubmittalRevisionModel,
)
from infrastructure.persistence.orm_models.submittal import (
    submittal_drawing_refs,
    submittal_location_refs,
)


def _submittal_to_domain(row: SubmittalModel) -> Submittal:
    return Submittal(
        id=row.id,
        project_id=row.project_id,
        number=row.number,
        spec_section_id=row.spec_section_id,
        package_id=row.package_id,
        vendor_id=row.vendor_id,
        commitment_id=row.commitment_id,
        submittal_type=row.submittal_type,
        category=row.category,
        lead_time_days=row.lead_time_days,
        required_on_site_date=row.required_on_site_date,
    )


class SqlAlchemySubmittalPackageRepository(SubmittalPackageRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, package: SubmittalPackage) -> SubmittalPackage:
        row = SubmittalPackageModel(
            project_id=package.project_id, name=package.name, description=package.description
        )
        self._session.add(row)
        self._session.flush()
        return SubmittalPackage(
            id=row.id, project_id=row.project_id, name=row.name, description=row.description
        )

    def list_by_project(self, project_id: int) -> list[SubmittalPackage]:
        rows = (
            self._session.execute(
                select(SubmittalPackageModel).where(SubmittalPackageModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [
            SubmittalPackage(id=r.id, project_id=r.project_id, name=r.name, description=r.description)
            for r in rows
        ]


def _review_status_to_domain(row: SubmittalReviewStatusModel) -> SubmittalReviewStatus:
    return SubmittalReviewStatus(
        id=row.id,
        project_id=row.project_id,
        code=row.code,
        label=row.label,
        gates_procurement=row.gates_procurement,
        is_terminal=row.is_terminal,
        sort_order=row.sort_order,
    )


class SqlAlchemySubmittalReviewStatusRepository(SubmittalReviewStatusRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, status: SubmittalReviewStatus) -> SubmittalReviewStatus:
        row = SubmittalReviewStatusModel(
            project_id=status.project_id,
            code=status.code,
            label=status.label,
            gates_procurement=status.gates_procurement,
            is_terminal=status.is_terminal,
            sort_order=status.sort_order,
        )
        self._session.add(row)
        self._session.flush()
        return _review_status_to_domain(row)

    def get(self, status_id: int) -> SubmittalReviewStatus | None:
        row = self._session.get(SubmittalReviewStatusModel, status_id)
        return _review_status_to_domain(row) if row else None

    def get_by_code(self, project_id: int, code: str) -> SubmittalReviewStatus | None:
        row = self._session.execute(
            select(SubmittalReviewStatusModel).where(
                SubmittalReviewStatusModel.project_id == project_id,
                SubmittalReviewStatusModel.code == code,
            )
        ).scalar_one_or_none()
        return _review_status_to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[SubmittalReviewStatus]:
        rows = (
            self._session.execute(
                select(SubmittalReviewStatusModel)
                .where(SubmittalReviewStatusModel.project_id == project_id)
                .order_by(SubmittalReviewStatusModel.sort_order)
            )
            .scalars()
            .all()
        )
        return [_review_status_to_domain(r) for r in rows]


class SqlAlchemySubmittalRequirementRepository(SubmittalRequirementRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, requirement: SubmittalRequirement) -> SubmittalRequirement:
        row = SubmittalRequirementModel(
            project_id=requirement.project_id,
            spec_section_id=requirement.spec_section_id,
            submittal_type=requirement.submittal_type,
            category=requirement.category,
        )
        self._session.add(row)
        self._session.flush()
        return SubmittalRequirement(
            id=row.id,
            project_id=row.project_id,
            spec_section_id=row.spec_section_id,
            submittal_type=row.submittal_type,
            category=row.category,
        )

    def list_by_project(
        self, project_id: int, spec_section_id: int | None = None
    ) -> list[SubmittalRequirement]:
        stmt = select(SubmittalRequirementModel).where(
            SubmittalRequirementModel.project_id == project_id
        )
        if spec_section_id is not None:
            stmt = stmt.where(SubmittalRequirementModel.spec_section_id == spec_section_id)
        rows = self._session.execute(stmt).scalars().all()
        return [
            SubmittalRequirement(
                id=r.id,
                project_id=r.project_id,
                spec_section_id=r.spec_section_id,
                submittal_type=r.submittal_type,
                category=r.category,
            )
            for r in rows
        ]


class SqlAlchemySubmittalRepository(SubmittalRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, submittal: Submittal) -> Submittal:
        row = SubmittalModel(
            project_id=submittal.project_id,
            number=submittal.number,
            spec_section_id=submittal.spec_section_id,
            package_id=submittal.package_id,
            vendor_id=submittal.vendor_id,
            commitment_id=submittal.commitment_id,
            submittal_type=submittal.submittal_type,
            category=submittal.category,
            lead_time_days=submittal.lead_time_days,
            required_on_site_date=submittal.required_on_site_date,
        )
        self._session.add(row)
        self._session.flush()
        return _submittal_to_domain(row)

    def get(self, submittal_id: int) -> Submittal | None:
        row = self._session.get(SubmittalModel, submittal_id)
        return _submittal_to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[Submittal]:
        rows = (
            self._session.execute(
                select(SubmittalModel).where(SubmittalModel.project_id == project_id)
            )
            .scalars()
            .all()
        )
        return [_submittal_to_domain(r) for r in rows]


class SqlAlchemySubmittalRevisionRepository(SubmittalRevisionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, row: SubmittalRevisionModel) -> SubmittalRevision:
        drawing_version_ids = list(
            self._session.execute(
                select(submittal_drawing_refs.c.drawing_version_id).where(
                    submittal_drawing_refs.c.submittal_revision_id == row.id
                )
            )
            .scalars()
            .all()
        )
        location_ids = list(
            self._session.execute(
                select(submittal_location_refs.c.location_id).where(
                    submittal_location_refs.c.submittal_revision_id == row.id
                )
            )
            .scalars()
            .all()
        )
        return SubmittalRevision(
            id=row.id,
            submittal_id=row.submittal_id,
            rev_label=row.rev_label,
            review_status_id=row.review_status_id,
            ball_in_court=BallInCourt(row.ball_in_court_role, row.ball_in_court_user_id),
            equipment_tag=row.equipment_tag,
            manufacturer=row.manufacturer,
            model=row.model,
            capacity_value=float(row.capacity_value) if row.capacity_value is not None else None,
            capacity_unit=row.capacity_unit,
            submitted_at=row.submitted_at,
            disposed_by_user_id=row.disposed_by_user_id,
            disposition_at=row.disposition_at,
            drawing_version_ids=drawing_version_ids,
            location_ids=location_ids,
        )

    def get(self, revision_id: int) -> SubmittalRevision | None:
        row = self._session.get(SubmittalRevisionModel, revision_id)
        return self._to_domain(row) if row else None

    def list_by_submittal(self, submittal_id: int) -> list[SubmittalRevision]:
        rows = (
            self._session.execute(
                select(SubmittalRevisionModel).where(
                    SubmittalRevisionModel.submittal_id == submittal_id
                )
            )
            .scalars()
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def add(self, revision: SubmittalRevision) -> SubmittalRevision:
        row = SubmittalRevisionModel(
            submittal_id=revision.submittal_id,
            rev_label=revision.rev_label,
            review_status_id=revision.review_status_id,
            ball_in_court_role=revision.ball_in_court.party_role,
            ball_in_court_user_id=revision.ball_in_court.user_id,
            equipment_tag=revision.equipment_tag,
            manufacturer=revision.manufacturer,
            model=revision.model,
            capacity_value=revision.capacity_value,
            capacity_unit=revision.capacity_unit,
            submitted_at=revision.submitted_at,
            disposed_by_user_id=revision.disposed_by_user_id,
            disposition_at=revision.disposition_at,
        )
        self._session.add(row)
        self._session.flush()
        for version_id in revision.drawing_version_ids:
            self._session.execute(
                submittal_drawing_refs.insert().values(
                    submittal_revision_id=row.id, drawing_version_id=version_id
                )
            )
        for location_id in revision.location_ids:
            self._session.execute(
                submittal_location_refs.insert().values(
                    submittal_revision_id=row.id, location_id=location_id
                )
            )
        self._session.flush()
        return self._to_domain(row)

    def update(self, revision: SubmittalRevision) -> SubmittalRevision:
        row = self._session.get(SubmittalRevisionModel, revision.id)
        row.review_status_id = revision.review_status_id
        row.ball_in_court_role = revision.ball_in_court.party_role
        row.ball_in_court_user_id = revision.ball_in_court.user_id
        row.submitted_at = revision.submitted_at
        row.disposed_by_user_id = revision.disposed_by_user_id
        row.disposition_at = revision.disposition_at
        self._session.flush()
        return self._to_domain(row)
