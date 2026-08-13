from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.purchase_order_use_cases import (
    AcknowledgePurchaseOrder,
    ApprovePurchaseOrder,
    CreatePurchaseOrder,
    GetPurchaseOrder,
    GetPurchaseOrderByNumber,
    ListPurchaseOrders,
    SubmitPurchaseOrderForApproval,
)
from domain.exceptions import InvalidTransition
from domain.value_objects import OrgScope

from tests.unit.application.fakes import FakeClock, InMemoryPurchaseOrderRepository


def _create(repo, **kwargs):
    defaults = dict(vendor_id=1, currency="USD", po_number="PO-1", org_scope=OrgScope(company_code="1000"))
    defaults.update(kwargs)
    return CreatePurchaseOrder(repo).execute(**defaults)


def test_create_and_get_by_number() -> None:
    repo = InMemoryPurchaseOrderRepository()
    _create(repo)
    po = GetPurchaseOrderByNumber(repo).execute("PO-1")
    assert po.status == "DRAFT"
    assert po.org_scope.company_code == "1000"


def test_get_by_number_not_found() -> None:
    repo = InMemoryPurchaseOrderRepository()
    with pytest.raises(NotFound):
        GetPurchaseOrderByNumber(repo).execute("does-not-exist")


def test_get_by_id() -> None:
    repo = InMemoryPurchaseOrderRepository()
    created = _create(repo)
    fetched = GetPurchaseOrder(repo).execute(created.id)
    assert fetched.po_number == "PO-1"


def test_submit_approve_acknowledge_full_cycle_stamps_changed_at() -> None:
    repo = InMemoryPurchaseOrderRepository()
    clock = FakeClock()
    _create(repo)

    po = SubmitPurchaseOrderForApproval(repo, clock).execute("PO-1")
    assert po.status == "PENDING_APPROVAL"
    assert po.changed_at == clock.now()

    po = ApprovePurchaseOrder(repo, clock).execute("PO-1")
    assert po.status == "OPEN"

    po = AcknowledgePurchaseOrder(repo, clock).execute("PO-1")
    assert po.acknowledged is True
    assert po.acknowledged_at == clock.now()


def test_approve_before_submit_raises() -> None:
    repo = InMemoryPurchaseOrderRepository()
    clock = FakeClock()
    _create(repo)
    with pytest.raises(InvalidTransition):
        ApprovePurchaseOrder(repo, clock).execute("PO-1")


def test_transition_not_found() -> None:
    repo = InMemoryPurchaseOrderRepository()
    clock = FakeClock()
    with pytest.raises(NotFound):
        SubmitPurchaseOrderForApproval(repo, clock).execute("does-not-exist")


def test_list_changed_since_filters_by_timestamp() -> None:
    repo = InMemoryPurchaseOrderRepository()
    clock = FakeClock()
    _create(repo, po_number="PO-1")
    _create(repo, po_number="PO-2")
    SubmitPurchaseOrderForApproval(repo, clock).execute("PO-1")  # stamps changed_at; PO-2 stays unstamped

    changed = ListPurchaseOrders(repo).execute(changed_since=clock.now())
    assert [po.po_number for po in changed] == ["PO-1"]

    everything = ListPurchaseOrders(repo).execute()
    assert len(everything) == 2
