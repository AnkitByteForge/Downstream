from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import Location


class LocationRepository(ABC):
    @abstractmethod
    def get(self, location_id: int) -> Location | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[Location]: ...

    @abstractmethod
    def add(self, location: Location) -> Location: ...
