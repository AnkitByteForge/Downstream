from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_create_contract,
    get_get_contract,
    get_list_contracts,
    require_csrf_token,
)
from api.pagination import PageParams, paginate
from api.schemas.contract import ContractOut, CreateContractRequest
from api.schemas.org_scope import OrgScopeOut
from application.exceptions import NotFound
from application.use_cases.contract_use_cases import CreateContract, GetContract, ListContracts
from domain.value_objects import OrgScope

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _out(c) -> ContractOut:
    return ContractOut(
        id=c.id,
        vendor_id=c.vendor_id,
        type=c.type,
        currency=c.currency,
        value=c.value,
        retention_pct=c.retention_pct,
        org_scope=OrgScopeOut(**vars(c.org_scope)),
    )


@router.get("", response_model=list[ContractOut])
def list_contracts(
    response: Response,
    use_case: ListContracts = Depends(get_list_contracts),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[ContractOut]:
    if not ctx.can_see("contracts"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(c) for c in page]


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    use_case: GetContract = Depends(get_get_contract),
    ctx: ActingContext = Depends(get_acting_context),
) -> ContractOut:
    ctx.require_scope("contracts")
    try:
        return _out(use_case.execute(contract_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
def create_contract(
    body: CreateContractRequest,
    use_case: CreateContract = Depends(get_create_contract),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> ContractOut:
    ctx.require_scope("contracts")
    return _out(
        use_case.execute(
            vendor_id=body.vendor_id,
            type=body.type,
            currency=body.currency,
            value=body.value,
            retention_pct=body.retention_pct,
            org_scope=OrgScope(company_code=body.company_code, plant=body.plant),
        )
    )
