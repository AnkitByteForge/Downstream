from __future__ import annotations

import pytest

from domain.entities.commitment import Commitment
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.state_machines import commitment_transitions as txn


def _commitment(status: str, committed=1000.0, relieved=0.0) -> Commitment:
    return Commitment(
        id=1,
        source_type="PO",
        cost_code_id=1,
        committed_amount=committed,
        currency="USD",
        relieved_amount=relieved,
        status=status,
    )


def test_relieve_partial() -> None:
    c = txn.relieve(_commitment("OPEN"), 400)
    assert c.relieved_amount == 400
    assert c.status == "PARTIALLY_RELIEVED"
    assert c.open_amount == 600


def test_relieve_full() -> None:
    c = txn.relieve(_commitment("OPEN"), 1000)
    assert c.status == "FULLY_RELIEVED"
    assert c.open_amount == 0


def test_relieve_further_from_partially_relieved() -> None:
    c = txn.relieve(_commitment("PARTIALLY_RELIEVED", relieved=400), 600)
    assert c.status == "FULLY_RELIEVED"
    assert c.relieved_amount == 1000


def test_relieve_rejects_fully_relieved() -> None:
    with pytest.raises(InvalidTransition):
        txn.relieve(_commitment("FULLY_RELIEVED", relieved=1000), 1)


def test_relieve_rejects_cancelled() -> None:
    with pytest.raises(InvalidTransition):
        txn.relieve(_commitment("CANCELLED"), 100)


def test_relieve_rejects_non_positive_amount() -> None:
    with pytest.raises(DomainRuleViolation):
        txn.relieve(_commitment("OPEN"), 0)


def test_relieve_rejects_amount_exceeding_committed() -> None:
    with pytest.raises(DomainRuleViolation):
        txn.relieve(_commitment("OPEN"), 1500)


def test_cancel_from_open() -> None:
    c = txn.cancel(_commitment("OPEN"))
    assert c.status == "CANCELLED"


def test_cancel_from_partially_relieved() -> None:
    c = txn.cancel(_commitment("PARTIALLY_RELIEVED", relieved=100))
    assert c.status == "CANCELLED"


def test_cancel_rejects_fully_relieved() -> None:
    with pytest.raises(InvalidTransition):
        txn.cancel(_commitment("FULLY_RELIEVED", relieved=1000))
