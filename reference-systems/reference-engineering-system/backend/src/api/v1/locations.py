from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.deps import ActingContext, get_acting_context, get_list_locations
from api.pagination import PageParams, paginate
from api.schemas.location import LocationOut
from application.use_cases.location_use_cases import ListLocations

router = APIRouter(tags=["locations"])


@router.get("/projects/{project_id}/locations", response_model=list[LocationOut])
def list_locations(
    project_id: int,
    response: Response,
    use_case: ListLocations = Depends(get_list_locations),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[LocationOut]:
    if not ctx.can_see("locations"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [LocationOut(**vars(loc)) for loc in page]
