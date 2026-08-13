from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.commitment import Commitment
from domain.repositories.commitment_repository import CommitmentRepository
from domain.value_objects import OrgScope
from infrastructure.persistence.orm_models import CommitmentModel


def _to_domain(row: CommitmentModel) -> Commitment:
    return Commitment(
        id=row.id,
        source_type=row.source_type,
        cost_code_id=row.cost_code_id,
        po_id=row.po_id,
        committed_amount=float(row.committed_amount),
        relieved_amount=float(row.relieved_amount),
        currency=row.currency,
        status=row.status,
        org_scope=OrgScope(
            company_code=row.company_code,
            plant=row.plant,
            purchasing_org=row.purchasing_org,
            business_unit=row.business_unit,
        ),
    )


class SqlAlchemyCommitmentRepository(CommitmentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, commitment: Commitment) -> Commitment:
        row = CommitmentModel(
            source_type=commitment.source_type,
            cost_code_id=commitment.cost_code_id,
            po_id=commitment.po_id,
            committed_amount=commitment.committed_amount,
            relieved_amount=commitment.relieved_amount,
            currency=commitment.currency,
            status=commitment.status,
            company_code=commitment.org_scope.company_code,
            plant=commitment.org_scope.plant,
            purchasing_org=commitment.org_scope.purchasing_org,
            business_unit=commitment.org_scope.business_unit,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)

    def get(self, commitment_id: int) -> Commitment | None:
        row = self._session.get(CommitmentModel, commitment_id)
        return _to_domain(row) if row else None

    def list_all(self) -> list[Commitment]:
        rows = self._session.execute(select(CommitmentModel)).scalars().all()
        return [_to_domain(r) for r in rows]

    def update(self, commitment: Commitment) -> Commitment:
        row = self._session.get(CommitmentModel, commitment.id)
        assert row is not None
        row.relieved_amount = commitment.relieved_amount
        row.status = commitment.status
        self._session.flush()
        return _to_domain(row)
