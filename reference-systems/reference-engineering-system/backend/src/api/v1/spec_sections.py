from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.deps import ActingContext, get_acting_context, get_list_spec_sections
from api.pagination import PageParams, paginate
from api.schemas.spec import SpecSectionOut
from application.use_cases.spec_use_cases import ListSpecSections

router = APIRouter(tags=["spec_sections"])


@router.get("/projects/{project_id}/spec_sections", response_model=list[SpecSectionOut])
def list_spec_sections(
    project_id: int,
    response: Response,
    use_case: ListSpecSections = Depends(get_list_spec_sections),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[SpecSectionOut]:
    if not ctx.can_see("spec_sections"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [SpecSectionOut(**vars(s)) for s in page]
