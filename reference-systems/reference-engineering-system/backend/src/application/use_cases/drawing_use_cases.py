from __future__ import annotations

from application.exceptions import NotFound
from domain.entities import Drawing, DrawingVersion
from domain.repositories import DrawingRepository, DrawingVersionRepository


class ListDrawings:
    def __init__(self, drawing_repo: DrawingRepository) -> None:
        self._drawing_repo = drawing_repo

    def execute(self, project_id: int) -> list[Drawing]:
        return self._drawing_repo.list_by_project(project_id)


class GetDrawing:
    def __init__(self, drawing_repo: DrawingRepository) -> None:
        self._drawing_repo = drawing_repo

    def execute(self, drawing_id: int) -> Drawing:
        drawing = self._drawing_repo.get(drawing_id)
        if drawing is None:
            raise NotFound("Drawing", drawing_id)
        return drawing


class ListDrawingVersions:
    """Backs the Drawing Revision Timeline — every version of a sheet, in
    issuance order, so the supersession chain is fully visible."""

    def __init__(self, version_repo: DrawingVersionRepository) -> None:
        self._version_repo = version_repo

    def execute(self, drawing_id: int) -> list[DrawingVersion]:
        versions = self._version_repo.list_by_drawing(drawing_id)
        return sorted(versions, key=lambda v: v.issuance_date)


class GetDrawingVersion:
    def __init__(self, version_repo: DrawingVersionRepository) -> None:
        self._version_repo = version_repo

    def execute(self, version_id: int) -> DrawingVersion:
        version = self._version_repo.get(version_id)
        if version is None:
            raise NotFound("DrawingVersion", version_id)
        return version
