from __future__ import annotations

from application.exceptions import NotFound
from domain.entities import Project
from domain.repositories import ProjectRepository


class ListProjects:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self) -> list[Project]:
        return self._project_repo.list()


class GetProject:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: int) -> Project:
        project = self._project_repo.get(project_id)
        if project is None:
            raise NotFound("Project", project_id)
        return project
