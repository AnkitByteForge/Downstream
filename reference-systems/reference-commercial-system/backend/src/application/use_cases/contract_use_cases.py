from __future__ import annotations

from domain.entities.contract import Contract
from domain.repositories.contract_repository import ContractRepository
from domain.value_objects import OrgScope

from application.exceptions import NotFound


class CreateContract:
    def __init__(self, repo: ContractRepository) -> None:
        self._repo = repo

    def execute(
        self,
        vendor_id: int,
        type: str,
        currency: str | None = None,
        value: float | None = None,
        retention_pct: float | None = None,
        org_scope: OrgScope | None = None,
    ) -> Contract:
        return self._repo.add(
            Contract(
                id=None,
                vendor_id=vendor_id,
                type=type,
                currency=currency,
                value=value,
                retention_pct=retention_pct,
                org_scope=org_scope or OrgScope(),
            )
        )


class ListContracts:
    def __init__(self, repo: ContractRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Contract]:
        return self._repo.list_all()


class GetContract:
    def __init__(self, repo: ContractRepository) -> None:
        self._repo = repo

    def execute(self, contract_id: int) -> Contract:
        contract = self._repo.get(contract_id)
        if contract is None:
            raise NotFound("Contract", contract_id)
        return contract
