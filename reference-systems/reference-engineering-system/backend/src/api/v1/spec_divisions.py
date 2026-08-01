from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import ActingContext, get_acting_context, get_list_spec_divisions
from api.schemas.spec import SpecDivisionOut
from application.use_cases.spec_use_cases import ListSpecDivisions

router = APIRouter(tags=["spec_divisions"])


@router.get("/spec_divisions", response_model=list[SpecDivisionOut])
def list_spec_divisions(
    use_case: ListSpecDivisions = Depends(get_list_spec_divisions),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[SpecDivisionOut]:
    """CSI MasterFormat divisions are global reference data, not project-
    scoped — authentication is required (any acting context), but no
    resource-type scope check applies, since PermissionScope binds to a
    project and this resource has none."""
    return [SpecDivisionOut(**vars(d)) for d in use_case.execute()]
