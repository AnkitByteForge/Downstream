from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import ActingContext, get_acting_context, get_get_project, get_list_projects
from api.schemas.project import ProjectOut
from application.exceptions import NotFound
from application.use_cases.project_use_cases import GetProject, ListProjects

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    use_case: ListProjects = Depends(get_list_projects),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[ProjectOut]:
    """Requires authentication. An authenticated actor only ever sees their
    own project — an integration credential or human session is bound to a
    single project, so the catalog is filtered to ``ctx.project_id`` rather
    than exposing every project (docs/03's hard project-partitioning
    boundary)."""
    return [ProjectOut(**vars(p)) for p in use_case.execute() if p.id == ctx.project_id]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    use_case: GetProject = Depends(get_get_project),
    ctx: ActingContext = Depends(get_acting_context),
) -> ProjectOut:
    ctx.require_project(project_id)
    try:
        return ProjectOut(**vars(use_case.execute(project_id)))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
