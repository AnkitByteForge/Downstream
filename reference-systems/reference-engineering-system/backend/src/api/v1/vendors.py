from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.deps import ActingContext, get_acting_context, get_list_vendors
from api.pagination import PageParams, paginate
from api.schemas.vendor import VendorOut
from application.use_cases.vendor_use_cases import ListVendors

router = APIRouter(tags=["vendors"])


@router.get("/projects/{project_id}/vendors", response_model=list[VendorOut])
def list_vendors(
    project_id: int,
    response: Response,
    use_case: ListVendors = Depends(get_list_vendors),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[VendorOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("vendors"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [VendorOut(**vars(v)) for v in page]
