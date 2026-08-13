from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.cost_code import CostCode
from domain.repositories.cost_code_repository import CostCodeRepository
from domain.value_objects import OrgScope
from infrastructure.persistence.orm_models import CostCodeModel


def _to_domain(row: CostCodeModel) -> CostCode:
    return CostCode(
        id=row.id,
        native_code=row.native_code,
        cost_code_format=row.cost_code_format,
        standard_ref=row.standard_ref,
        parent_id=row.parent_id,
        org_scope=OrgScope(
            company_code=row.company_code,
            plant=row.plant,
            purchasing_org=row.purchasing_org,
            business_unit=row.business_unit,
        ),
        budget_baseline=_f(row.budget_baseline),
        budget_current=_f(row.budget_current),
        committed=_f(row.committed),
        actual=_f(row.actual),
        etc=_f(row.etc),
        eac=_f(row.eac),
    )


def _f(value) -> float | None:
    return float(value) if value is not None else None


class SqlAlchemyCostCodeRepository(CostCodeRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, cost_code: CostCode) -> CostCode:
        row = CostCodeModel(
            native_code=cost_code.native_code,
            cost_code_format=cost_code.cost_code_format,
            standard_ref=cost_code.standard_ref,
            parent_id=cost_code.parent_id,
            company_code=cost_code.org_scope.company_code,
            plant=cost_code.org_scope.plant,
            purchasing_org=cost_code.org_scope.purchasing_org,
            business_unit=cost_code.org_scope.business_unit,
            budget_baseline=cost_code.budget_baseline,
            budget_current=cost_code.budget_current,
            committed=cost_code.committed,
            actual=cost_code.actual,
            etc=cost_code.etc,
            eac=cost_code.eac,
        )
        self._session.add(row)
        self._session.flush()
        return _to_domain(row)

    def get(self, cost_code_id: int) -> CostCode | None:
        row = self._session.get(CostCodeModel, cost_code_id)
        return _to_domain(row) if row else None

    def get_by_native_code(self, native_code: str) -> CostCode | None:
        # native_code is not asserted globally unique at the DB level — the
        # same code string can legitimately recur under a different
        # OrgScope (ADR-012's multi-company-code posture). scalar_one_or_none
        # would raise MultipleResultsFound in that case; this returns the
        # first match instead, matching the port's single-result contract
        # without assuming uniqueness the schema doesn't actually enforce.
        row = self._session.execute(
            select(CostCodeModel).where(CostCodeModel.native_code == native_code).limit(1)
        ).scalar_one_or_none()
        return _to_domain(row) if row else None

    def list_all(self) -> list[CostCode]:
        rows = self._session.execute(select(CostCodeModel)).scalars().all()
        return [_to_domain(r) for r in rows]
