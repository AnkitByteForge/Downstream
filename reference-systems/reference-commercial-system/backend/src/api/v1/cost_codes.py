from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_create_cost_code,
    get_get_cost_code,
    get_list_cost_codes,
    require_csrf_token,
)
from api.pagination import PageParams, paginate
from api.schemas.cost_code import CostCodeOut, CreateCostCodeRequest
from api.schemas.org_scope import OrgScopeOut
from application.exceptions import NotFound
from application.use_cases.cost_code_use_cases import CreateCostCode, GetCostCode, ListCostCodes
from domain.value_objects import OrgScope

router = APIRouter(prefix="/cost_codes", tags=["cost_codes"])


def _out(c) -> CostCodeOut:
    return CostCodeOut(
        id=c.id,
        native_code=c.native_code,
        cost_code_format=c.cost_code_format,
        standard_ref=c.standard_ref,
        parent_id=c.parent_id,
        org_scope=OrgScopeOut(**vars(c.org_scope)),
        budget_baseline=c.budget_baseline,
        budget_current=c.budget_current,
        committed=c.committed,
        actual=c.actual,
        etc=c.etc,
        eac=c.eac,
    )


@router.get("", response_model=list[CostCodeOut])
def list_cost_codes(
    response: Response,
    use_case: ListCostCodes = Depends(get_list_cost_codes),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[CostCodeOut]:
    if not ctx.can_see("cost_codes"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(c) for c in page]


@router.get("/{cost_code_id}", response_model=CostCodeOut)
def get_cost_code(
    cost_code_id: int,
    use_case: GetCostCode = Depends(get_get_cost_code),
    ctx: ActingContext = Depends(get_acting_context),
) -> CostCodeOut:
    ctx.require_scope("cost_codes")
    try:
        return _out(use_case.execute(cost_code_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("", response_model=CostCodeOut, status_code=status.HTTP_201_CREATED)
def create_cost_code(
    body: CreateCostCodeRequest,
    use_case: CreateCostCode = Depends(get_create_cost_code),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> CostCodeOut:
    ctx.require_scope("cost_codes")
    return _out(
        use_case.execute(
            native_code=body.native_code,
            cost_code_format=body.cost_code_format,
            standard_ref=body.standard_ref,
            parent_id=body.parent_id,
            org_scope=OrgScope(company_code=body.company_code, plant=body.plant),
            budget_baseline=body.budget_baseline,
            budget_current=body.budget_current,
            committed=body.committed,
            actual=body.actual,
            etc=body.etc,
            eac=body.eac,
        )
    )
