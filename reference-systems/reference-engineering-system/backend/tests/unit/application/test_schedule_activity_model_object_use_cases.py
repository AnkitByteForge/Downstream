from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.model_object_use_cases import GetModelObject, ListModelObjects
from application.use_cases.schedule_activity_use_cases import (
    GetScheduleActivity,
    ListScheduleActivities,
)
from domain.entities.model_object import ModelObject
from domain.entities.schedule_activity import ScheduleActivity
from tests.unit.application.fakes import (
    InMemoryModelObjectRepository,
    InMemoryScheduleActivityRepository,
)


def make_activity(activity_id: int | None = None, project_id: int = 1) -> ScheduleActivity:
    return ScheduleActivity(
        id=activity_id, project_id=project_id, activity_code="3410", type="PROCUREMENT"
    )


def make_object(object_id: int | None = None, project_id: int = 1) -> ModelObject:
    return ModelObject(
        id=object_id, project_id=project_id, discipline_code="E", appearance_profile="INSTALL"
    )


def test_list_schedule_activities_filters_by_project():
    repo = InMemoryScheduleActivityRepository(
        [make_activity(1, project_id=1), make_activity(2, project_id=2)]
    )
    assert len(ListScheduleActivities(repo).execute(1)) == 1
    assert ListScheduleActivities(repo).execute(99) == []


def test_get_schedule_activity_returns_or_raises():
    repo = InMemoryScheduleActivityRepository([make_activity(1)])
    found = GetScheduleActivity(repo).execute(1)
    assert found.activity_code == "3410"
    with pytest.raises(NotFound):
        GetScheduleActivity(repo).execute(99)


def test_list_model_objects_filters_by_project():
    repo = InMemoryModelObjectRepository([make_object(1, project_id=1), make_object(2, project_id=2)])
    assert len(ListModelObjects(repo).execute(1)) == 1
    assert ListModelObjects(repo).execute(99) == []


def test_get_model_object_returns_or_raises():
    repo = InMemoryModelObjectRepository([make_object(1)])
    found = GetModelObject(repo).execute(1)
    assert found.appearance_profile == "INSTALL"
    with pytest.raises(NotFound):
        GetModelObject(repo).execute(99)
