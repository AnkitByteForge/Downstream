from __future__ import annotations

from domain.entities.submittal import SubmittalRequirement
from domain.repositories.submittal_repository import SubmittalRequirementRepository


class ListSubmittalRequirements:
    def __init__(self, repo: SubmittalRequirementRepository) -> None:
        self._repo = repo

    def execute(self, project_id: int, spec_section_id: int | None = None) -> list[SubmittalRequirement]:
        return self._repo.list_by_project(project_id, spec_section_id)
