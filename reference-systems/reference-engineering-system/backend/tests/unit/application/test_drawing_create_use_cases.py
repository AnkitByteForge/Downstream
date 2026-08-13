from __future__ import annotations

from datetime import date, datetime, timezone

from application.exceptions import NotFound
from application.use_cases.drawing_use_cases import CreateDrawing, CreateDrawingVersion
from domain.value_objects import RevisionCloud
import pytest
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryDrawingRepository,
    InMemoryDrawingVersionRepository,
)


def test_create_drawing_creates_a_new_row_and_reports_created_true():
    repo = InMemoryDrawingRepository([])
    use_case = CreateDrawing(repo)

    drawing, created = use_case.execute(1, "E0.4", "Air Handler Replacement Schedule", "E")

    assert created is True
    assert drawing.id is not None
    assert drawing.project_id == 1
    assert drawing.sheet_number == "E0.4"
    assert drawing.title == "Air Handler Replacement Schedule"
    assert drawing.discipline_code == "E"
    assert repo.get(drawing.id) == drawing


def test_create_drawing_is_idempotent_on_project_and_sheet_number():
    repo = InMemoryDrawingRepository([])
    use_case = CreateDrawing(repo)

    first, first_created = use_case.execute(1, "E0.4", "Air Handler Replacement Schedule", "E")
    second, second_created = use_case.execute(1, "E0.4", "Air Handler Replacement Schedule", "E")

    assert first_created is True
    assert second_created is False
    assert first.id == second.id
    assert len(repo.list_by_project(1)) == 1


def test_create_drawing_same_sheet_number_different_project_is_not_a_duplicate():
    """Natural key is (project_id, sheet_number), not sheet_number alone --
    two different real projects could both have a sheet numbered E0.4."""
    repo = InMemoryDrawingRepository([])
    use_case = CreateDrawing(repo)

    drawing_a, created_a = use_case.execute(1, "E0.4", "Project A's E0.4", "E")
    drawing_b, created_b = use_case.execute(2, "E0.4", "Project B's E0.4", "E")

    assert created_a is True
    assert created_b is True
    assert drawing_a.id != drawing_b.id


def _clock() -> FakeClock:
    return FakeClock(datetime(2026, 8, 13, 12, 0, 0, tzinfo=timezone.utc))


def test_create_drawing_version_creates_a_new_draft_row():
    drawing_repo = InMemoryDrawingRepository([])
    drawing, _ = CreateDrawing(drawing_repo).execute(1, "E0.4", "Air Handler Schedule", "E")

    version_repo = InMemoryDrawingVersionRepository([])
    use_case = CreateDrawingVersion(drawing_repo, version_repo, _clock())

    version, created = use_case.execute(drawing.id, "Rev A", "E")

    assert created is True
    assert version.drawing_id == drawing.id
    assert version.revision_label == "Rev A"
    assert version.status == "DRAFT"
    assert version.issuance_date == date(2026, 8, 13)
    assert version.revision_clouds == []


def test_create_drawing_version_is_idempotent_on_drawing_and_revision_label():
    drawing_repo = InMemoryDrawingRepository([])
    drawing, _ = CreateDrawing(drawing_repo).execute(1, "E0.4", "Air Handler Schedule", "E")
    version_repo = InMemoryDrawingVersionRepository([])
    use_case = CreateDrawingVersion(drawing_repo, version_repo, _clock())

    first, first_created = use_case.execute(drawing.id, "Rev A", "E")
    second, second_created = use_case.execute(drawing.id, "Rev A", "E")

    assert first_created is True
    assert second_created is False
    assert first.id == second.id
    assert len(version_repo.list_by_drawing(drawing.id)) == 1


def test_create_drawing_version_preserves_source_evidence_ref_on_revision_clouds():
    drawing_repo = InMemoryDrawingRepository([])
    drawing, _ = CreateDrawing(drawing_repo).execute(1, "E0.4", "Air Handler Schedule", "E")
    version_repo = InMemoryDrawingVersionRepository([])
    use_case = CreateDrawingVersion(drawing_repo, version_repo, _clock())

    cloud = RevisionCloud(
        area="New Unit block, row AH-9A",
        delta_number=1,
        description="fed_from_panel = MR4",
        source_evidence_ref="dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A",
    )
    version, _ = use_case.execute(drawing.id, "Rev A", "E", [cloud])

    assert version.revision_clouds == [cloud]
    assert version.revision_clouds[0].source_evidence_ref == (
        "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A"
    )


def test_create_drawing_version_for_unknown_drawing_raises_not_found():
    drawing_repo = InMemoryDrawingRepository([])
    version_repo = InMemoryDrawingVersionRepository([])
    use_case = CreateDrawingVersion(drawing_repo, version_repo, _clock())

    with pytest.raises(NotFound):
        use_case.execute(999, "Rev A", "E")


def test_create_drawing_version_same_label_different_drawing_is_not_a_duplicate():
    drawing_repo = InMemoryDrawingRepository([])
    drawing_a, _ = CreateDrawing(drawing_repo).execute(1, "E0.4", "Sheet A", "E")
    drawing_b, _ = CreateDrawing(drawing_repo).execute(1, "E0.6", "Sheet B", "E")
    version_repo = InMemoryDrawingVersionRepository([])
    use_case = CreateDrawingVersion(drawing_repo, version_repo, _clock())

    version_a, created_a = use_case.execute(drawing_a.id, "Rev A", "E")
    version_b, created_b = use_case.execute(drawing_b.id, "Rev A", "E")

    assert created_a is True
    assert created_b is True
    assert version_a.id != version_b.id
