from __future__ import annotations

from application.exceptions import NotFound
from domain.entities.model_object import ModelObject
from domain.repositories.model_object_repository import ModelObjectRepository


class ListModelObjects:
    def __init__(self, repo: ModelObjectRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int) -> list[ModelObject]:
        return self._repo.list_by_project(project_id)


class GetModelObject:
    def __init__(self, repo: ModelObjectRepository) -> None:
        self._repo = repo

    def execute(self, model_object_id: int) -> ModelObject:
        obj = self._repo.get(model_object_id)
        if obj is None:
            raise NotFound("ModelObject", model_object_id)
        return obj
