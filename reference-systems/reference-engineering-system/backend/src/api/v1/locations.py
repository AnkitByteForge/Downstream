from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_list_locations
from api.schemas.location import LocationOut
from application.use_cases.location_use_cases import ListLocations

router = APIRouter(tags=["locations"])


@router.get("/projects/{project_id}/locations", response_model=list[LocationOut])
def list_locations(
    project_id: int, use_case: ListLocations = Depends(get_list_locations)
) -> list[LocationOut]:
    return [LocationOut(**vars(loc)) for loc in use_case.execute(project_id)]
