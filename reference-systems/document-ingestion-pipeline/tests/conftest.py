"""Shared test fixtures."""

import json
from pathlib import Path

import pytest

from dip.diff.models import EquipmentRow

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_synthetic_rows(file_name: str) -> tuple[str, list[EquipmentRow]]:
    payload = json.loads((FIXTURES_DIR / file_name).read_text(encoding="utf-8"))
    assert payload["SYNTHETIC"] is True, f"{file_name} must be explicitly marked SYNTHETIC"
    rows = [EquipmentRow.model_validate(r) for r in payload["rows"]]
    return payload["sheet"], rows


@pytest.fixture()
def synthetic_rev_a() -> tuple[str, list[EquipmentRow]]:
    return _load_synthetic_rows("synthetic_rev_a.json")


@pytest.fixture()
def synthetic_rev_b() -> tuple[str, list[EquipmentRow]]:
    return _load_synthetic_rows("synthetic_rev_b.json")
