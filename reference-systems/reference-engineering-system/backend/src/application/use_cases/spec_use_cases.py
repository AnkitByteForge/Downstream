from __future__ import annotations

from domain.entities import SpecDivision, SpecSection
from domain.repositories import SpecDivisionRepository, SpecSectionRepository


class ListSpecDivisions:
    def __init__(self, division_repo: SpecDivisionRepository) -> None:
        self._division_repo = division_repo

    def execute(self) -> list[SpecDivision]:
        return self._division_repo.list()


class ListSpecSections:
    def __init__(self, section_repo: SpecSectionRepository) -> None:
        self._section_repo = section_repo

    def execute(self, project_id: int) -> list[SpecSection]:
        return self._section_repo.list_by_project(project_id)
