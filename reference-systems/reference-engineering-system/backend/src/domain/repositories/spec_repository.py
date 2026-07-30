from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import SpecDivision, SpecSection


class SpecDivisionRepository(ABC):
    @abstractmethod
    def list(self) -> list[SpecDivision]: ...

    @abstractmethod
    def add(self, division: SpecDivision) -> SpecDivision: ...


class SpecSectionRepository(ABC):
    @abstractmethod
    def get(self, section_id: int) -> SpecSection | None: ...

    @abstractmethod
    def get_by_number(self, project_id: int, number: str) -> SpecSection | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[SpecSection]: ...

    @abstractmethod
    def add(self, section: SpecSection) -> SpecSection: ...
