from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.contract_use_cases import CreateContract, GetContract, ListContracts
from application.use_cases.cost_code_use_cases import CreateCostCode, GetCostCode, ListCostCodes
from domain.value_objects import OrgScope

from tests.unit.application.fakes import InMemoryContractRepository, InMemoryCostCodeRepository


def test_create_and_get_cost_code() -> None:
    repo = InMemoryCostCodeRepository()
    created = CreateCostCode(repo).execute(
        native_code="26-200",
        cost_code_format="CSI_MASTERFORMAT",
        standard_ref="26 24 13",
        org_scope=OrgScope(company_code="2000"),
    )
    fetched = GetCostCode(repo).execute(created.id)
    assert fetched.standard_ref == "26 24 13"
    assert fetched.org_scope.company_code == "2000"


def test_list_cost_codes() -> None:
    repo = InMemoryCostCodeRepository()
    CreateCostCode(repo).execute(native_code="A", cost_code_format="CUSTOM")
    CreateCostCode(repo).execute(native_code="B", cost_code_format="CUSTOM")
    assert len(ListCostCodes(repo).execute()) == 2


def test_get_cost_code_not_found() -> None:
    repo = InMemoryCostCodeRepository()
    with pytest.raises(NotFound):
        GetCostCode(repo).execute(999)


def test_create_and_get_contract() -> None:
    repo = InMemoryContractRepository()
    created = CreateContract(repo).execute(vendor_id=1, type="SUBCONTRACT", currency="INR", value=500000)
    fetched = GetContract(repo).execute(created.id)
    assert fetched.type == "SUBCONTRACT"
    assert fetched.value == 500000


def test_list_contracts() -> None:
    repo = InMemoryContractRepository()
    CreateContract(repo).execute(vendor_id=1, type="BLANKET")
    assert len(ListContracts(repo).execute()) == 1


def test_get_contract_not_found() -> None:
    repo = InMemoryContractRepository()
    with pytest.raises(NotFound):
        GetContract(repo).execute(999)
