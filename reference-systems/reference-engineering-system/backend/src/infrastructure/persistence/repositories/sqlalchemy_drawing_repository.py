from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import Drawing, DrawingVersion
from domain.repositories import DrawingRepository, DrawingVersionRepository
from domain.value_objects import RevisionCloud
from infrastructure.persistence.orm_models import DrawingModel, DrawingVersionModel, RevisionCloudModel
from infrastructure.persistence.orm_models.drawing import drawing_version_locations


def _drawing_to_domain(row: DrawingModel) -> Drawing:
    return Drawing(
        id=row.id,
        project_id=row.project_id,
        sheet_number=row.sheet_number,
        title=row.title,
        discipline_code=row.discipline_code,
        current_version_id=row.current_version_id,
    )


class SqlAlchemyDrawingRepository(DrawingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, drawing_id: int) -> Drawing | None:
        row = self._session.get(DrawingModel, drawing_id)
        return _drawing_to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[Drawing]:
        rows = (
            self._session.execute(select(DrawingModel).where(DrawingModel.project_id == project_id))
            .scalars()
            .all()
        )
        return [_drawing_to_domain(r) for r in rows]

    def add(self, drawing: Drawing) -> Drawing:
        row = DrawingModel(
            project_id=drawing.project_id,
            sheet_number=drawing.sheet_number,
            title=drawing.title,
            discipline_code=drawing.discipline_code,
            current_version_id=drawing.current_version_id,
        )
        self._session.add(row)
        self._session.flush()
        return _drawing_to_domain(row)

    def update(self, drawing: Drawing) -> Drawing:
        row = self._session.get(DrawingModel, drawing.id)
        row.title = drawing.title
        row.current_version_id = drawing.current_version_id
        self._session.flush()
        return _drawing_to_domain(row)


class SqlAlchemyDrawingVersionRepository(DrawingVersionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, row: DrawingVersionModel) -> DrawingVersion:
        clouds = (
            self._session.execute(
                select(RevisionCloudModel).where(RevisionCloudModel.version_id == row.id)
            )
            .scalars()
            .all()
        )
        location_ids = list(
            self._session.execute(
                select(drawing_version_locations.c.location_id).where(
                    drawing_version_locations.c.version_id == row.id
                )
            )
            .scalars()
            .all()
        )
        return DrawingVersion(
            id=row.id,
            drawing_id=row.drawing_id,
            revision_label=row.revision_label,
            issuance_date=row.issuance_date,
            status=row.status,
            discipline_code=row.discipline_code,
            superseded_by_id=row.superseded_by_id,
            revision_clouds=[
                RevisionCloud(
                    area=c.area,
                    delta_number=c.delta_number,
                    description=c.description,
                    source_evidence_ref=c.source_evidence_ref,
                )
                for c in clouds
            ],
            location_ids=location_ids,
        )

    def get(self, version_id: int) -> DrawingVersion | None:
        row = self._session.get(DrawingVersionModel, version_id)
        return self._to_domain(row) if row else None

    def list_by_drawing(self, drawing_id: int) -> list[DrawingVersion]:
        rows = (
            self._session.execute(
                select(DrawingVersionModel).where(DrawingVersionModel.drawing_id == drawing_id)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def add(self, version: DrawingVersion) -> DrawingVersion:
        row = DrawingVersionModel(
            drawing_id=version.drawing_id,
            revision_label=version.revision_label,
            issuance_date=version.issuance_date,
            status=version.status,
            discipline_code=version.discipline_code,
            superseded_by_id=version.superseded_by_id,
        )
        self._session.add(row)
        self._session.flush()
        for cloud in version.revision_clouds:
            self._session.add(
                RevisionCloudModel(
                    version_id=row.id,
                    area=cloud.area,
                    delta_number=cloud.delta_number,
                    description=cloud.description,
                    source_evidence_ref=cloud.source_evidence_ref,
                )
            )
        for location_id in version.location_ids:
            self._session.execute(
                drawing_version_locations.insert().values(
                    version_id=row.id, location_id=location_id
                )
            )
        self._session.flush()
        return self._to_domain(row)

    def update(self, version: DrawingVersion) -> DrawingVersion:
        row = self._session.get(DrawingVersionModel, version.id)
        row.status = version.status
        row.superseded_by_id = version.superseded_by_id
        self._session.execute(
            RevisionCloudModel.__table__.delete().where(
                RevisionCloudModel.version_id == version.id
            )
        )
        for cloud in version.revision_clouds:
            self._session.add(
                RevisionCloudModel(
                    version_id=version.id,
                    area=cloud.area,
                    delta_number=cloud.delta_number,
                    description=cloud.description,
                    source_evidence_ref=cloud.source_evidence_ref,
                )
            )
        self._session.flush()
        return self._to_domain(row)
