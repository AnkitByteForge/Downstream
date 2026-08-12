from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    ensure_resource_in_project,
    get_acting_context,
    get_get_model_object,
    get_list_model_objects,
)
from api.pagination import PageParams, paginate
from api.schemas.model_object import ModelObjectOut
from application.exceptions import NotFound
from application.use_cases.model_object_use_cases import GetModelObject, ListModelObjects
from domain.entities.model_object import ModelObject

router = APIRouter(tags=["model_objects"])


def _out(obj: ModelObject) -> ModelObjectOut:
    return ModelObjectOut(
        id=obj.id,
        project_id=obj.project_id,
        discipline_code=obj.discipline_code,
        appearance_profile=obj.appearance_profile,
        location_id=obj.location_id,
        resource_link_id=obj.resource_link_id,
    )


@router.get("/projects/{project_id}/model_objects", response_model=list[ModelObjectOut])
def list_model_objects(
    project_id: int,
    response: Response,
    use_case: ListModelObjects = Depends(get_list_model_objects),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[ModelObjectOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("model_objects"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(o) for o in page]


@router.get(
    "/projects/{project_id}/model_objects/{model_object_id}",
    response_model=ModelObjectOut,
)
def get_model_object(
    project_id: int,
    model_object_id: int,
    use_case: GetModelObject = Depends(get_get_model_object),
    ctx: ActingContext = Depends(get_acting_context),
) -> ModelObjectOut:
    ctx.require_project(project_id)
    ctx.require_scope("model_objects")
    try:
        obj = use_case.execute(model_object_id)
        ensure_resource_in_project(obj.project_id, project_id)
        return _out(obj)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
