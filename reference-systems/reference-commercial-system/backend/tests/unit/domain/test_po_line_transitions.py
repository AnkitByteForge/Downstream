from __future__ import annotations

import pytest

from domain.entities.purchase_order import POLine
from domain.exceptions import InvalidTransition
from domain.state_machines import po_line_transitions as txn


def _line(lifecycle_position: str) -> POLine:
    return POLine(
        id=1,
        po_id=1,
        line_no=1,
        description="Test line",
        quantity=1,
        uom="EA",
        unit_price=100,
        value=100,
        lifecycle_position=lifecycle_position,
    )


def test_issue_line_from_draft() -> None:
    line = txn.issue_line(_line("draft"))
    assert line.lifecycle_position == "issued"


def test_issue_line_rejects_non_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.issue_line(_line("issued"))


def test_start_fabrication_from_issued() -> None:
    line = txn.start_fabrication(_line("issued"))
    assert line.lifecycle_position == "in_fabrication"


def test_start_fabrication_rejects_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.start_fabrication(_line("draft"))


def test_ship_from_in_fabrication() -> None:
    line = txn.ship(_line("in_fabrication"))
    assert line.lifecycle_position == "shipped"


def test_ship_rejects_issued() -> None:
    with pytest.raises(InvalidTransition):
        txn.ship(_line("issued"))


def test_install_from_shipped() -> None:
    line = txn.install(_line("shipped"))
    assert line.lifecycle_position == "installed"


def test_install_rejects_in_fabrication() -> None:
    with pytest.raises(InvalidTransition):
        txn.install(_line("in_fabrication"))


def test_cannot_skip_a_stage() -> None:
    """draft -> in_fabrication directly must never succeed — the whole
    point of a strictly sequential lifecycle (ADR-013)."""
    with pytest.raises(InvalidTransition):
        txn.start_fabrication(_line("draft"))


def test_installed_is_terminal() -> None:
    with pytest.raises(InvalidTransition):
        txn.issue_line(_line("installed"))
