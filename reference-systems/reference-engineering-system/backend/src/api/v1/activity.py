from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_list_activity
from api.schemas.webhook import ActivityEntryOut
from application.use_cases.webhook_use_cases import ListActivity

router = APIRouter(tags=["activity"])


@router.get("/projects/{project_id}/activity", response_model=list[ActivityEntryOut])
def list_activity(
    project_id: int, use_case: ListActivity = Depends(get_list_activity)
) -> list[ActivityEntryOut]:
    return [ActivityEntryOut(**vars(entry)) for entry in use_case.execute(project_id)]
