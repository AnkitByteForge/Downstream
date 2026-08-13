from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.contract import Contract
from domain.repositories.contract_repository import ContractRepository
from domain.value_objects import OrgScope
from infrastructure.persistence.orm_models import ContractModel


def _to_domain(row: ContractModel) -> Contract:
    return Contract(
        id=row.id,
        vendor_id=row.vendor_id,
        type=row.type,
        currency=row.currency,
        value=float(row.value) if row.value is not None else None,
        retention_pct=float(row.retention_pct) if row.retention_pct is not None else None,
        org_scope=OrgScope(
            company_code=row.company_code,
            plant=row.plant,
            purchasing_org=row.purchasing_org,
            business_unit=row.business_unit,
        ),
    )


class SqlAlchemyContractRepository(ContractRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, contract: Contract) -> Contract:
        row = ContractModel(
            vendor_id=contract.vendor_id,
            type=contract.type,
            currency=contract.currency,
            value=contract.value,
            retention_pct=contract.retention_pct,
            company_code=contract.org_scope.company_code,
            plant=contract.org_scope.plant,
            purchasing_org=contract.org_scope.purchasing_org,
            business_unit=contract.org_scope.business_unit,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)

    def get(self, contract_id: int) -> Contract | None:
        row = self._session.get(ContractModel, contract_id)
        return _to_domain(row) if row else None

    def list_all(self) -> list[Contract]:
        rows = self._session.execute(select(ContractModel)).scalars().all()
        return [_to_domain(r) for r in rows]
