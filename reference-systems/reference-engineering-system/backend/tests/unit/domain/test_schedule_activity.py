from __future__ import annotations

import pytest

from domain.entities.schedule_activity import SCHEDULE_ACTIVITY_TYPES, ScheduleActivity
from domain.exceptions import DomainError


@pytest.mark.parametrize("activity_type", SCHEDULE_ACTIVITY_TYPES)
def test_accepts_every_closed_type(activity_type: str) -> None:
    activity = ScheduleActivity(
        id=None, project_id=1, activity_code="A-100", type=activity_type
    )
    assert activity.type == activity_type


def test_rejects_invalid_type() -> None:
    with pytest.raises(DomainError):
        ScheduleActivity(id=None, project_id=1, activity_code="A-100", type="INVALID")


def test_defaults_are_empty_and_wbs_is_nullable() -> None:
    activity = ScheduleActivity(id=None, project_id=1, activity_code="3410", type="PROCUREMENT")
    assert activity.wbs is None
    assert activity.predecessor_ids == []
    assert activity.successor_ids == []
    assert activity.linked_submittal_ids == []
    assert activity.delivery_milestone is None
