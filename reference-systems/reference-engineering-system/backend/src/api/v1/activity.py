from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import ActingContext, get_acting_context, get_list_activity
from api.schemas.webhook import ActivityEntryOut
from application.use_cases.webhook_use_cases import ListActivity

router = APIRouter(tags=["activity"])


@router.get("/projects/{project_id}/activity", response_model=list[ActivityEntryOut])
def list_activity(
    project_id: int,
    use_case: ListActivity = Depends(get_list_activity),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[ActivityEntryOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("activity"):
        return []
    return [ActivityEntryOut(**vars(entry)) for entry in use_case.execute(project_id)]
