from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.model_object import ModelObject


class ModelObjectRepository(ABC):
    """Persistence port for ModelObject (RES-5). Read-only surface — no
    `update`, nothing mutates a model object through this system."""

    @abstractmethod
    def get(self, model_object_id: int) -> ModelObject | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[ModelObject]: ...

    @abstractmethod
    def add(self, model_object: ModelObject) -> ModelObject: ...
