from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.vendor import Commitment, Vendor
from domain.repositories.vendor_repository import CommitmentRepository, VendorRepository
from infrastructure.persistence.orm_models import CommitmentModel, VendorModel


def _vendor_to_domain(row: VendorModel) -> Vendor:
    return Vendor(id=row.id, project_id=row.project_id, name=row.name)


def _commitment_to_domain(row: CommitmentModel) -> Commitment:
    return Commitment(
        id=row.id,
        project_id=row.project_id,
        vendor_id=row.vendor_id,
        cost_code=row.cost_code,
        description=row.description,
        amount=float(row.amount),
        spec_section_id=row.spec_section_id,
    )


class SqlAlchemyVendorRepository(VendorRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, vendor: Vendor) -> Vendor:
        row = VendorModel(project_id=vendor.project_id, name=vendor.name)
        self._session.add(row)
        self._session.flush()
        return _vendor_to_domain(row)

    def get(self, vendor_id: int) -> Vendor | None:
        row = self._session.get(VendorModel, vendor_id)
        return _vendor_to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[Vendor]:
        rows = (
            self._session.execute(select(VendorModel).where(VendorModel.project_id == project_id))
            .scalars()
            .all()
        )
        return [_vendor_to_domain(r) for r in rows]


class SqlAlchemyCommitmentRepository(CommitmentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, commitment: Commitment) -> Commitment:
        row = CommitmentModel(
            project_id=commitment.project_id,
            vendor_id=commitment.vendor_id,
            cost_code=commitment.cost_code,
            description=commitment.description,
            amount=commitment.amount,
            spec_section_id=commitment.spec_section_id,
        )
        self._session.add(row)
        self._session.flush()
        return _commitment_to_domain(row)

    def get(self, commitment_id: int) -> Commitment | None:
        row = self._session.get(CommitmentModel, commitment_id)
        return _commitment_to_domain(row) if row else None
