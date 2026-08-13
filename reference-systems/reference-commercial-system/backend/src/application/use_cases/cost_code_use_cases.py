from __future__ import annotations

from domain.entities.cost_code import CostCode
from domain.repositories.cost_code_repository import CostCodeRepository
from domain.value_objects import OrgScope

from application.exceptions import NotFound


class CreateCostCode:
    def __init__(self, repo: CostCodeRepository) -> None:
        self._repo = repo

    def execute(
        self,
        native_code: str,
        cost_code_format: str,
        standard_ref: str | None = None,
        parent_id: int | None = None,
        org_scope: OrgScope | None = None,
        budget_baseline: float | None = None,
        budget_current: float | None = None,
        committed: float | None = None,
        actual: float | None = None,
        etc: float | None = None,
        eac: float | None = None,
    ) -> CostCode:
        return self._repo.add(
            CostCode(
                id=None,
                native_code=native_code,
                cost_code_format=cost_code_format,
                standard_ref=standard_ref,
                parent_id=parent_id,
                org_scope=org_scope or OrgScope(),
                budget_baseline=budget_baseline,
                budget_current=budget_current,
                committed=committed,
                actual=actual,
                etc=etc,
                eac=eac,
            )
        )


class ListCostCodes:
    def __init__(self, repo: CostCodeRepository) -> None:
        self._repo = repo

    def execute(self) -> list[CostCode]:
        return self._repo.list_all()


class GetCostCode:
    def __init__(self, repo: CostCodeRepository) -> None:
        self._repo = repo

    def execute(self, cost_code_id: int) -> CostCode:
        cost_code = self._repo.get(cost_code_id)
        if cost_code is None:
            raise NotFound("CostCode", cost_code_id)
        return cost_code
