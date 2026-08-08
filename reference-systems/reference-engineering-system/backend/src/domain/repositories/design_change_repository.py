from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.design_change import DesignChange


class DesignChangeRepository(ABC):
    """Persistence port for DesignChange (RES-4). Supports only what the
    application/API layer genuinely needs: look up one change, list a
    project's changes, and add/update for state-machine transitions."""

    @abstractmethod
    def get(self, design_change_id: int) -> DesignChange | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[DesignChange]: ...

    @abstractmethod
    def add(self, design_change: DesignChange) -> DesignChange: ...

    @abstractmethod
    def update(self, design_change: DesignChange) -> DesignChange: ...
