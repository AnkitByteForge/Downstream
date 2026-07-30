from __future__ import annotations

from domain.entities import Location
from domain.repositories import LocationRepository


class ListLocations:
    def __init__(self, location_repo: LocationRepository) -> None:
        self._location_repo = location_repo

    def execute(self, project_id: int) -> list[Location]:
        return self._location_repo.list_by_project(project_id)
