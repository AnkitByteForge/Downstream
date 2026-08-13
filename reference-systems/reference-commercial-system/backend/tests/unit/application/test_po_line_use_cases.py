from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.po_line_use_cases import (
    CreatePOLine,
    GetPOLine,
    InstallPOLine,
    IssuePOLine,
    ListPOLines,
    ShipPOLine,
    StartFabricationPOLine,
)
from domain.exceptions import InvalidTransition

from tests.unit.application.fakes import InMemoryPOLineRepository


def _create(repo, **kwargs):
    defaults = dict(po_id=1, line_no=1, description="X", quantity=1, uom="EA", unit_price=10, value=10)
    defaults.update(kwargs)
    return CreatePOLine(repo).execute(**defaults)


def test_create_get_list_line() -> None:
    repo = InMemoryPOLineRepository()
    created = _create(repo)
    assert created.lifecycle_position == "draft"
    fetched = GetPOLine(repo).execute(created.id)
    assert fetched.description == "X"
    assert len(ListPOLines(repo).execute(po_id=1)) == 1


def test_full_fabrication_lifecycle() -> None:
    repo = InMemoryPOLineRepository()
    line = _create(repo)
    line = IssuePOLine(repo).execute(line.id)
    assert line.lifecycle_position == "issued"
    line = StartFabricationPOLine(repo).execute(line.id)
    assert line.lifecycle_position == "in_fabrication"
    line = ShipPOLine(repo).execute(line.id)
    assert line.lifecycle_position == "shipped"
    line = InstallPOLine(repo).execute(line.id)
    assert line.lifecycle_position == "installed"


def test_cannot_skip_stage_via_use_case() -> None:
    repo = InMemoryPOLineRepository()
    line = _create(repo)
    with pytest.raises(InvalidTransition):
        StartFabricationPOLine(repo).execute(line.id)


def test_get_not_found() -> None:
    repo = InMemoryPOLineRepository()
    with pytest.raises(NotFound):
        GetPOLine(repo).execute(999)
