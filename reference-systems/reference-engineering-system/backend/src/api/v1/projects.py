from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_get_project, get_list_projects
from api.schemas.project import ProjectOut
from application.use_cases.project_use_cases import GetProject, ListProjects

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(use_case: ListProjects = Depends(get_list_projects)) -> list[ProjectOut]:
    return [ProjectOut(**vars(p)) for p in use_case.execute()]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, use_case: GetProject = Depends(get_get_project)) -> ProjectOut:
    return ProjectOut(**vars(use_case.execute(project_id)))
