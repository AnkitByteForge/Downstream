from __future__ import annotations

from datetime import date

import pytest

from domain.entities import DrawingVersion
from domain.exceptions import InvalidTransition
from domain.state_machines import drawing_version_transitions
from domain.value_objects import RevisionCloud


def make_version(status: str = "DRAFT") -> DrawingVersion:
    return DrawingVersion(
        id=1,
        drawing_id=1,
        revision_label="Rev C",
        issuance_date=date(2026, 7, 28),
        status=status,
        discipline_code="M",
    )


def test_issue_version_from_draft():
    version = make_version("DRAFT")
    issued = drawing_version_transitions.issue_version(version)
    assert issued.status == "ISSUED"


def test_issue_version_from_non_draft_raises():
    with pytest.raises(InvalidTransition):
        drawing_version_transitions.issue_version(make_version("ISSUED"))


def test_mark_revised_attaches_clouds():
    version = make_version("ISSUED")
    cloud = RevisionCloud(area="Grid B-4", delta_number=1, description="Duct rerouted")
    revised = drawing_version_transitions.mark_revised(version, [cloud])
    assert revised.status == "REVISED"
    assert revised.revision_clouds == [cloud]


def test_supersede_sets_pointer_and_terminal_status():
    version = make_version("REVISED")
    superseded = drawing_version_transitions.supersede(version, superseded_by_id=99)
    assert superseded.status == "SUPERSEDED"
    assert superseded.superseded_by_id == 99


def test_cannot_transition_out_of_superseded():
    version = make_version("SUPERSEDED")
    with pytest.raises(InvalidTransition):
        drawing_version_transitions.supersede(version, superseded_by_id=1)
