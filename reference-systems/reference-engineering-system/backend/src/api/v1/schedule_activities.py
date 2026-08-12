from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    ensure_resource_in_project,
    get_acting_context,
    get_get_schedule_activity,
    get_list_schedule_activities,
)
from api.pagination import PageParams, paginate
from api.schemas.schedule_activity import ScheduleActivityOut
from application.exceptions import NotFound
from application.use_cases.schedule_activity_use_cases import (
    GetScheduleActivity,
    ListScheduleActivities,
)
from domain.entities.schedule_activity import ScheduleActivity

router = APIRouter(tags=["schedule_activities"])


def _out(activity: ScheduleActivity) -> ScheduleActivityOut:
    return ScheduleActivityOut(
        id=activity.id,
        project_id=activity.project_id,
        activity_code=activity.activity_code,
        type=activity.type,
        wbs=activity.wbs,
        predecessor_ids=activity.predecessor_ids,
        successor_ids=activity.successor_ids,
        linked_submittal_ids=activity.linked_submittal_ids,
        delivery_milestone=activity.delivery_milestone,
    )


@router.get("/projects/{project_id}/schedule_activities", response_model=list[ScheduleActivityOut])
def list_schedule_activities(
    project_id: int,
    response: Response,
    use_case: ListScheduleActivities = Depends(get_list_schedule_activities),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[ScheduleActivityOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("schedule_activities"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(a) for a in page]


@router.get(
    "/projects/{project_id}/schedule_activities/{schedule_activity_id}",
    response_model=ScheduleActivityOut,
)
def get_schedule_activity(
    project_id: int,
    schedule_activity_id: int,
    use_case: GetScheduleActivity = Depends(get_get_schedule_activity),
    ctx: ActingContext = Depends(get_acting_context),
) -> ScheduleActivityOut:
    ctx.require_project(project_id)
    ctx.require_scope("schedule_activities")
    try:
        activity = use_case.execute(schedule_activity_id)
        ensure_resource_in_project(activity.project_id, project_id)
        return _out(activity)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
