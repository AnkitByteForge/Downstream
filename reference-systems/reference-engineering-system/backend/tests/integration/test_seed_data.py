from __future__ import annotations

from sqlalchemy import text

from infrastructure.persistence.repositories.sqlalchemy_design_change_repository import (
    SqlAlchemyDesignChangeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_drawing_repository import (
    SqlAlchemyDrawingRepository,
    SqlAlchemyDrawingVersionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_rfi_repository import SqlAlchemyRFIRepository
from infrastructure.persistence.repositories.sqlalchemy_schedule_activity_repository import (
    SqlAlchemyScheduleActivityRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_submittal_repository import (
    SqlAlchemySubmittalRevisionRepository,
    SqlAlchemySubmittalReviewStatusRepository,
)
from seed.meridian_tower import seed


def _truncate_all(db_session) -> None:
    """The canonical seed runs against the shared dev database, which may
    already have committed seed rows (unique emails etc.). This test clears
    every table inside its own rolled-back transaction so it passes whether
    or not run_seed has already been run — the transaction rolls back, so a
    populated dev database is left exactly as it was."""
    tables = db_session.execute(
        text("select tablename from pg_tables where schemaname = 'public'")
    ).scalars().all()
    joined = ", ".join(f'"{t}"' for t in tables)
    db_session.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))


def test_canonical_seed_design_change_and_e_drawing(db_session):
    """The RES-4D canonical seed (Canonical_Demo_Dataset.md §8 Stage B2):
    ASI-07 is ISSUED, cites the SUB-118 load increase, and drives the
    DWG-E-1.1 Rev 0 -> Rev 1 supersession without becoming a new RFI trigger."""
    _truncate_all(db_session)
    result = seed(db_session)

    design_change_repo = SqlAlchemyDesignChangeRepository(db_session)
    rfi_repo = SqlAlchemyRFIRepository(db_session)
    drawing_repo = SqlAlchemyDrawingRepository(db_session)
    version_repo = SqlAlchemyDrawingVersionRepository(db_session)
    revision_repo = SqlAlchemySubmittalRevisionRepository(db_session)
    review_status_repo = SqlAlchemySubmittalReviewStatusRepository(db_session)

    design_change = design_change_repo.get(result["design_change_id"])
    assert design_change.display_number == "ASI-07"
    assert design_change.type == "ASI"
    assert design_change.status == "ISSUED"
    assert design_change.issued_at is not None
    assert "CA-RTU-55" in design_change.change_reason

    # Scenario-A trigger stays untouched: RFI-214 remains CLOSED and is the
    # only RFI; the ASI does not re-open or add any RFI.
    rfis = rfi_repo.list_by_project(result["project_id"])
    assert len(rfis) == 1
    assert rfis[0].display_number == "RFI-214"
    assert rfis[0].status == "CLOSED"

    # ASI-07 is historical/scene-setting, linked to its originating RFI (the
    # domain model's source_rfi_id relationship) rather than a separate
    # trigger — RFI-214 stays the lone trigger chain (RES-4E).
    assert design_change.source_rfi_id == rfis[0].id

    # The design change affects the switchgear spec section relevant to the
    # upsized RTU (240 A MCA) and at least one drawing version.
    assert design_change.affected_spec_section_ids
    assert design_change.affected_drawing_version_ids

    drawing = drawing_repo.get(result["design_change_drawing_id"])
    assert drawing.sheet_number == "E-1.1"
    assert drawing.discipline_code == "E"

    versions = version_repo.list_by_drawing(drawing.id)
    by_label = {v.revision_label: v for v in versions}
    assert set(by_label) == {"Rev 0", "Rev 1"}
    assert by_label["Rev 0"].status == "SUPERSEDED"
    assert by_label["Rev 1"].status == "ISSUED"
    assert by_label["Rev 1"].id == drawing.current_version_id
    assert by_label["Rev 0"].superseded_by_id == by_label["Rev 1"].id

    # The ASI affects exactly the current (Rev 1) version — the issue-side of
    # the DesignChange -> DrawingVersion chain (ADR-007).
    assert design_change.affected_drawing_version_ids == [by_label["Rev 1"].id]

    # SUB-118 and its MCA/FLA table are preserved (canonical §7): Rev 1 still
    # reaches NO_EXCEPTIONS_TAKEN with the upsized 240 A MCA / 200 A FLA.
    net_status = review_status_repo.get_by_code(result["project_id"], "NO_EXCEPTIONS_TAKEN")
    revisions = revision_repo.list_by_submittal(result["submittal_id"])
    rev_1 = next(r for r in revisions if r.rev_label == "Rev 1")
    assert rev_1.review_status_id == net_status.id
    assert rev_1.capacity_value == 240
    assert rev_1.capacity_unit == "A_MCA"
    assert rev_1.fla_value == 200


def test_canonical_seed_schedule_activity_3410(db_session):
    """RES-5D canonical seed (Canonical_Demo_Dataset.md §10/§13): the frozen
    Scenario A "sched_3410" / "Schedule Activity 3410" row exists, is
    project-scoped to Meridian Tower, and carries no invented relationships
    or wbs (ADR-008) — the canonical row itself specifies none."""
    _truncate_all(db_session)
    result = seed(db_session)

    schedule_activity_repo = SqlAlchemyScheduleActivityRepository(db_session)
    activity = schedule_activity_repo.get(result["schedule_activity_id"])

    assert activity.project_id == result["project_id"]
    assert activity.activity_code == "3410"
    assert activity.type == "PROCUREMENT"
    assert activity.wbs is None
    assert activity.predecessor_ids == []
    assert activity.successor_ids == []
    assert activity.linked_submittal_ids == []
    assert activity.delivery_milestone is None

    activities = schedule_activity_repo.list_by_project(result["project_id"])
    assert len(activities) == 1