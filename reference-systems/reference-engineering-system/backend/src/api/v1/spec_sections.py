from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import ActingContext, get_acting_context, get_list_spec_sections
from api.schemas.spec import SpecSectionOut
from application.use_cases.spec_use_cases import ListSpecSections

router = APIRouter(tags=["spec_sections"])


@router.get("/projects/{project_id}/spec_sections", response_model=list[SpecSectionOut])
def list_spec_sections(
    project_id: int,
    use_case: ListSpecSections = Depends(get_list_spec_sections),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[SpecSectionOut]:
    if not ctx.can_see("spec_sections"):
        return []
    return [SpecSectionOut(**vars(s)) for s in use_case.execute(project_id)]
