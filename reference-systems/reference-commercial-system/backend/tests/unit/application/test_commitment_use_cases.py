from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.commitment_use_cases import (
    CancelCommitment,
    CreateCommitment,
    GetCommitment,
    ListCommitments,
    RelieveCommitment,
)
from domain.exceptions import DomainRuleViolation

from tests.unit.application.fakes import InMemoryCommitmentRepository


def test_create_and_get_commitment() -> None:
    repo = InMemoryCommitmentRepository()
    created = CreateCommitment(repo).execute(
        source_type="PO", cost_code_id=1, committed_amount=1000, currency="USD", po_id=1
    )
    fetched = GetCommitment(repo).execute(created.id)
    assert fetched.status == "OPEN"
    assert fetched.open_amount == 1000


def test_relieve_partial_then_full() -> None:
    repo = InMemoryCommitmentRepository()
    c = CreateCommitment(repo).execute(
        source_type="PO", cost_code_id=1, committed_amount=1000, currency="USD"
    )
    c = RelieveCommitment(repo).execute(c.id, 400)
    assert c.status == "PARTIALLY_RELIEVED"
    c = RelieveCommitment(repo).execute(c.id, 600)
    assert c.status == "FULLY_RELIEVED"


def test_relieve_over_committed_amount_raises() -> None:
    repo = InMemoryCommitmentRepository()
    c = CreateCommitment(repo).execute(
        source_type="PO", cost_code_id=1, committed_amount=1000, currency="USD"
    )
    with pytest.raises(DomainRuleViolation):
        RelieveCommitment(repo).execute(c.id, 5000)


def test_cancel_commitment() -> None:
    repo = InMemoryCommitmentRepository()
    c = CreateCommitment(repo).execute(
        source_type="PO", cost_code_id=1, committed_amount=1000, currency="USD"
    )
    c = CancelCommitment(repo).execute(c.id)
    assert c.status == "CANCELLED"


def test_list_commitments() -> None:
    repo = InMemoryCommitmentRepository()
    CreateCommitment(repo).execute(source_type="PO", cost_code_id=1, committed_amount=1, currency="USD")
    CreateCommitment(repo).execute(source_type="PO", cost_code_id=2, committed_amount=2, currency="USD")
    assert len(ListCommitments(repo).execute()) == 2


def test_get_not_found() -> None:
    repo = InMemoryCommitmentRepository()
    with pytest.raises(NotFound):
        GetCommitment(repo).execute(999)
