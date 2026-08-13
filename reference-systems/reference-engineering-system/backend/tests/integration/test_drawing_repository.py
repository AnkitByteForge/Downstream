from __future__ import annotations

from datetime import date

from domain.entities.project import Discipline, Project
from domain.entities import Drawing, DrawingVersion
from domain.value_objects import RevisionCloud
from infrastructure.persistence.repositories.sqlalchemy_drawing_repository import (
    SqlAlchemyDrawingRepository,
    SqlAlchemyDrawingVersionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)


def _seed_project(session):
    SqlAlchemyDisciplineRepository(session).add(Discipline(code="IT", name="Integration Test Discipline"))
    return SqlAlchemyProjectRepository(session).add(
        Project(id=None, name="Integration Test Project", spec_format="MF2020")
    )


def test_revision_cloud_source_evidence_ref_round_trips_through_the_real_database(db_session):
    """ADR-009/E.3: the additive source_evidence_ref field must survive a
    real Postgres round trip (add -> flush -> re-fetch via a fresh get),
    not just an in-process dataclass equality check."""
    project = _seed_project(db_session)
    drawing_repo = SqlAlchemyDrawingRepository(db_session)
    version_repo = SqlAlchemyDrawingVersionRepository(db_session)

    drawing = drawing_repo.add(
        Drawing(
            id=None,
            project_id=project.id,
            sheet_number="E0.4",
            title="Air Handler Replacement Schedule",
            discipline_code="IT",
            current_version_id=None,
        )
    )

    version = version_repo.add(
        DrawingVersion(
            id=None,
            drawing_id=drawing.id,
            revision_label="Rev A",
            issuance_date=date(2026, 8, 13),
            status="DRAFT",
            discipline_code="IT",
            revision_clouds=[
                RevisionCloud(
                    area="New Unit block, row AH-9A",
                    delta_number=1,
                    description="Promoted from real E0.4 evidence",
                    source_evidence_ref="dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A",
                )
            ],
        )
    )

    fetched = version_repo.get(version.id)
    assert len(fetched.revision_clouds) == 1
    assert fetched.revision_clouds[0].source_evidence_ref == (
        "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A"
    )


def test_revision_cloud_without_source_evidence_ref_defaults_to_none(db_session):
    """Backward compatibility: a RevisionCloud built the pre-ADR-009 way
    (no source_evidence_ref kwarg at all) must still round-trip cleanly as
    None — proving existing callers (e.g. the Meridian Tower seed script)
    are unaffected."""
    project = _seed_project(db_session)
    drawing_repo = SqlAlchemyDrawingRepository(db_session)
    version_repo = SqlAlchemyDrawingVersionRepository(db_session)

    drawing = drawing_repo.add(
        Drawing(
            id=None,
            project_id=project.id,
            sheet_number="E-1.1",
            title="Electrical Plan",
            discipline_code="IT",
            current_version_id=None,
        )
    )
    version = version_repo.add(
        DrawingVersion(
            id=None,
            drawing_id=drawing.id,
            revision_label="Rev 0",
            issuance_date=date(2026, 8, 13),
            status="DRAFT",
            discipline_code="IT",
            revision_clouds=[
                RevisionCloud(area="Grid B-4", delta_number=1, description="Duct rerouted"),
            ],
        )
    )

    fetched = version_repo.get(version.id)
    assert fetched.revision_clouds[0].source_evidence_ref is None
