from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import Discipline, Project


class ProjectRepository(ABC):
    @abstractmethod
    def get(self, project_id: int) -> Project | None: ...

    @abstractmethod
    def list(self) -> list[Project]: ...

    @abstractmethod
    def add(self, project: Project) -> Project: ...


class DisciplineRepository(ABC):
    @abstractmethod
    def get(self, code: str) -> Discipline | None: ...

    @abstractmethod
    def list(self) -> list[Discipline]: ...

    @abstractmethod
    def add(self, discipline: Discipline) -> Discipline: ...
