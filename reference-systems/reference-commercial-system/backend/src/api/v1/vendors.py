from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_add_vendor_scope_view,
    get_approve_vendor,
    get_blacklist_vendor,
    get_create_vendor,
    get_get_vendor,
    get_list_vendor_scope_views,
    get_list_vendors,
    get_prequalify_vendor,
    get_suspend_vendor,
    require_csrf_token,
)
from api.pagination import PageParams, paginate
from api.schemas.vendor import (
    CreateVendorRequest,
    CreateVendorScopeViewRequest,
    VendorOut,
    VendorScopeViewOut,
)
from application.exceptions import NotFound
from application.use_cases.vendor_use_cases import (
    AddVendorScopeView,
    ApproveVendor,
    BlacklistVendor,
    CreateVendor,
    GetVendor,
    ListVendors,
    ListVendorScopeViews,
    PrequalifyVendor,
    SuspendVendor,
)
from domain.exceptions import InvalidTransition

router = APIRouter(prefix="/vendors", tags=["vendors"])


def _out(v) -> VendorOut:
    return VendorOut(
        id=v.id, name=v.name, qualification_status=v.qualification_status, performance_score=v.performance_score
    )


@router.get("", response_model=list[VendorOut])
def list_vendors(
    response: Response,
    use_case: ListVendors = Depends(get_list_vendors),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[VendorOut]:
    if not ctx.can_see("vendors"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(v) for v in page]


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(
    vendor_id: int,
    use_case: GetVendor = Depends(get_get_vendor),
    ctx: ActingContext = Depends(get_acting_context),
) -> VendorOut:
    ctx.require_scope("vendors")
    try:
        return _out(use_case.execute(vendor_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor(
    body: CreateVendorRequest,
    use_case: CreateVendor = Depends(get_create_vendor),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorOut:
    ctx.require_scope("vendors")
    return _out(use_case.execute(body.name))


def _transition_route(use_case, vendor_id: int):
    try:
        return _out(use_case.execute(vendor_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.patch("/{vendor_id}/prequalify", response_model=VendorOut)
def prequalify_vendor(
    vendor_id: int,
    use_case: PrequalifyVendor = Depends(get_prequalify_vendor),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorOut:
    ctx.require_scope("vendors")
    return _transition_route(use_case, vendor_id)


@router.patch("/{vendor_id}/approve", response_model=VendorOut)
def approve_vendor(
    vendor_id: int,
    use_case: ApproveVendor = Depends(get_approve_vendor),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorOut:
    ctx.require_scope("vendors")
    return _transition_route(use_case, vendor_id)


@router.patch("/{vendor_id}/suspend", response_model=VendorOut)
def suspend_vendor(
    vendor_id: int,
    use_case: SuspendVendor = Depends(get_suspend_vendor),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorOut:
    ctx.require_scope("vendors")
    return _transition_route(use_case, vendor_id)


@router.patch("/{vendor_id}/blacklist", response_model=VendorOut)
def blacklist_vendor(
    vendor_id: int,
    use_case: BlacklistVendor = Depends(get_blacklist_vendor),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorOut:
    ctx.require_scope("vendors")
    return _transition_route(use_case, vendor_id)


@router.get("/{vendor_id}/scope_views", response_model=list[VendorScopeViewOut])
def list_vendor_scope_views(
    vendor_id: int,
    use_case: ListVendorScopeViews = Depends(get_list_vendor_scope_views),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[VendorScopeViewOut]:
    ctx.require_scope("vendors")
    return [
        VendorScopeViewOut(
            id=v.id,
            vendor_id=v.vendor_id,
            company_code=v.company_code,
            purchasing_org=v.purchasing_org,
            blocked=v.blocked,
            purchasing_terms=v.purchasing_terms,
        )
        for v in use_case.execute(vendor_id)
    ]


@router.post("/{vendor_id}/scope_views", response_model=VendorScopeViewOut, status_code=status.HTTP_201_CREATED)
def add_vendor_scope_view(
    vendor_id: int,
    body: CreateVendorScopeViewRequest,
    use_case: AddVendorScopeView = Depends(get_add_vendor_scope_view),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> VendorScopeViewOut:
    ctx.require_scope("vendors")
    v = use_case.execute(vendor_id, body.company_code, body.purchasing_org, body.blocked)
    return VendorScopeViewOut(
        id=v.id,
        vendor_id=v.vendor_id,
        company_code=v.company_code,
        purchasing_org=v.purchasing_org,
        blocked=v.blocked,
        purchasing_terms=v.purchasing_terms,
    )
