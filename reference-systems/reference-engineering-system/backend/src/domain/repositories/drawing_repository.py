from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import Drawing, DrawingVersion


class DrawingRepository(ABC):
    @abstractmethod
    def get(self, drawing_id: int) -> Drawing | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[Drawing]: ...

    @abstractmethod
    def add(self, drawing: Drawing) -> Drawing: ...

    @abstractmethod
    def update(self, drawing: Drawing) -> Drawing: ...


class DrawingVersionRepository(ABC):
    @abstractmethod
    def get(self, version_id: int) -> DrawingVersion | None: ...

    @abstractmethod
    def list_by_drawing(self, drawing_id: int) -> list[DrawingVersion]: ...

    @abstractmethod
    def add(self, version: DrawingVersion) -> DrawingVersion: ...

    @abstractmethod
    def update(self, version: DrawingVersion) -> DrawingVersion: ...
