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

    @abstractmethod
    def get_by_sheet_number(self, project_id: int, sheet_number: str) -> Drawing | None:
        """Drawing's natural key (project_id, sheet_number) -- E.4's
        idempotent-creation lookup (ADR-009)."""
        ...


class DrawingVersionRepository(ABC):
    @abstractmethod
    def get(self, version_id: int) -> DrawingVersion | None: ...

    @abstractmethod
    def list_by_drawing(self, drawing_id: int) -> list[DrawingVersion]: ...

    @abstractmethod
    def add(self, version: DrawingVersion) -> DrawingVersion: ...

    @abstractmethod
    def update(self, version: DrawingVersion) -> DrawingVersion: ...

    @abstractmethod
    def get_by_drawing_and_label(self, drawing_id: int, revision_label: str) -> DrawingVersion | None:
        """DrawingVersion's natural key (drawing_id, revision_label) --
        E.4's idempotent-creation lookup (ADR-009)."""
        ...
