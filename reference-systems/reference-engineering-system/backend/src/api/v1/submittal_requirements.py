from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.deps import ActingContext, get_acting_context, get_list_submittal_requirements
from api.pagination import PageParams, paginate
from api.schemas.submittal import SubmittalRequirementOut
from application.use_cases.submittal_requirement_use_cases import ListSubmittalRequirements

router = APIRouter(tags=["submittal_requirements"])


@router.get(
    "/projects/{project_id}/submittal_requirements", response_model=list[SubmittalRequirementOut]
)
def list_submittal_requirements(
    project_id: int,
    response: Response,
    spec_section_id: int | None = None,
    use_case: ListSubmittalRequirements = Depends(get_list_submittal_requirements),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[SubmittalRequirementOut]:
    if not ctx.can_see("submittal_requirements"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id, spec_section_id), page_params)
    response.headers["X-Total"] = str(total)
    return [SubmittalRequirementOut(**vars(r)) for r in page]
