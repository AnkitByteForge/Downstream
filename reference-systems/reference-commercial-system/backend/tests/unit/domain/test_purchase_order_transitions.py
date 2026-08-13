from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities.purchase_order import PurchaseOrder
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.state_machines import purchase_order_transitions as txn

NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)


def _po(status: str, **overrides) -> PurchaseOrder:
    defaults = dict(id=1, po_number="4500000001", vendor_id=1, currency="USD", status=status)
    defaults.update(overrides)
    return PurchaseOrder(**defaults)


def test_submit_for_approval_from_draft() -> None:
    po = txn.submit_for_approval(_po("DRAFT"))
    assert po.status == "PENDING_APPROVAL"


def test_submit_for_approval_rejects_non_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.submit_for_approval(_po("OPEN"))


def test_approve_from_pending_approval() -> None:
    po = txn.approve(_po("PENDING_APPROVAL"))
    assert po.status == "OPEN"


def test_approve_rejects_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.approve(_po("DRAFT"))


def test_reject_from_pending_approval() -> None:
    po = txn.reject(_po("PENDING_APPROVAL"))
    assert po.status == "REJECTED"


@pytest.mark.parametrize("status", ["DRAFT", "PENDING_APPROVAL"])
def test_withdraw_from_draft_or_pending(status: str) -> None:
    po = txn.withdraw(_po(status))
    assert po.status == "WITHDRAWN"


def test_withdraw_rejects_open() -> None:
    with pytest.raises(InvalidTransition):
        txn.withdraw(_po("OPEN"))


@pytest.mark.parametrize("status", ["DRAFT", "PENDING_APPROVAL", "OPEN"])
def test_cancel_from_draft_pending_or_open(status: str) -> None:
    po = txn.cancel(_po(status))
    assert po.status == "CANCELED"


def test_cancel_rejects_closed() -> None:
    with pytest.raises(InvalidTransition):
        txn.cancel(_po("CLOSED"))


def test_acknowledge_from_open() -> None:
    po = txn.acknowledge(_po("OPEN"), NOW)
    assert po.acknowledged is True
    assert po.acknowledged_at == NOW


def test_acknowledge_rejects_non_open() -> None:
    with pytest.raises(InvalidTransition):
        txn.acknowledge(_po("DRAFT"), NOW)


def test_acknowledge_rejects_already_acknowledged() -> None:
    with pytest.raises(DomainRuleViolation):
        txn.acknowledge(_po("OPEN", acknowledged=True), NOW)


def test_hold_from_open() -> None:
    po = txn.hold(_po("OPEN"))
    assert po.status == "ON_HOLD"


def test_hold_rejects_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.hold(_po("DRAFT"))


def test_release_hold_from_on_hold() -> None:
    po = txn.release_hold(_po("ON_HOLD"))
    assert po.status == "OPEN"


def test_release_hold_rejects_open() -> None:
    with pytest.raises(InvalidTransition):
        txn.release_hold(_po("OPEN"))


def test_amend_from_open() -> None:
    po = txn.amend(_po("OPEN"))
    assert po.status == "PENDING_CHANGE_APPROVAL"


def test_approve_amendment_from_pending_change_approval() -> None:
    po = txn.approve_amendment(_po("PENDING_CHANGE_APPROVAL"))
    assert po.status == "OPEN"


def test_approve_amendment_rejects_open() -> None:
    with pytest.raises(InvalidTransition):
        txn.approve_amendment(_po("OPEN"))


@pytest.mark.parametrize("status", ["OPEN", "ON_HOLD"])
def test_close_from_open_or_on_hold(status: str) -> None:
    po = txn.close(_po(status))
    assert po.status == "CLOSED"
    assert po.delivery_completed is True
    assert po.final_invoice is True


def test_close_rejects_draft() -> None:
    with pytest.raises(InvalidTransition):
        txn.close(_po("DRAFT"))


def test_finally_close_from_closed() -> None:
    po = txn.finally_close(_po("CLOSED"))
    assert po.status == "FINALLY_CLOSED"


def test_finally_close_rejects_open() -> None:
    with pytest.raises(InvalidTransition):
        txn.finally_close(_po("OPEN"))
