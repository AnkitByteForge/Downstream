from __future__ import annotations

import pytest

from domain.entities.model_object import APPEARANCE_PROFILES, ModelObject
from domain.exceptions import DomainError


@pytest.mark.parametrize("profile", APPEARANCE_PROFILES)
def test_accepts_every_closed_appearance_profile(profile: str) -> None:
    obj = ModelObject(id=None, project_id=1, discipline_code="E", appearance_profile=profile)
    assert obj.appearance_profile == profile


def test_rejects_invalid_appearance_profile() -> None:
    with pytest.raises(DomainError):
        ModelObject(id=None, project_id=1, discipline_code="E", appearance_profile="INVALID")


def test_location_and_resource_link_default_to_none() -> None:
    obj = ModelObject(id=None, project_id=1, discipline_code="E", appearance_profile="INSTALL")
    assert obj.location_id is None
    assert obj.resource_link_id is None
