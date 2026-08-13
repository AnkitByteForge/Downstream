from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from domain.entities.purchase_order import PurchaseOrder
from domain.repositories.purchase_order_repository import PurchaseOrderRepository
from domain.state_machines import purchase_order_transitions as txn
from domain.value_objects import OrgScope

from application.exceptions import NotFound
from application.ports import ClockPort


class CreatePurchaseOrder:
    def __init__(self, repo: PurchaseOrderRepository) -> None:
        self._repo = repo

    def execute(
        self,
        vendor_id: int,
        currency: str,
        po_number: str | None = None,
        contract_id: int | None = None,
        payment_terms: str | None = None,
        org_scope: OrgScope | None = None,
    ) -> PurchaseOrder:
        return self._repo.add(
            PurchaseOrder(
                id=None,
                po_number=po_number,
                vendor_id=vendor_id,
                currency=currency,
                contract_id=contract_id,
                payment_terms=payment_terms,
                org_scope=org_scope or OrgScope(),
            )
        )


class ListPurchaseOrders:
    def __init__(self, repo: PurchaseOrderRepository) -> None:
        self._repo = repo

    def execute(self, changed_since: datetime | None = None) -> list[PurchaseOrder]:
        if changed_since is not None:
            return self._repo.list_changed_since(changed_since)
        return self._repo.list_all()


class GetPurchaseOrder:
    def __init__(self, repo: PurchaseOrderRepository) -> None:
        self._repo = repo

    def execute(self, po_id: int) -> PurchaseOrder:
        po = self._repo.get(po_id)
        if po is None:
            raise NotFound("PurchaseOrder", po_id)
        return po


class GetPurchaseOrderByNumber:
    def __init__(self, repo: PurchaseOrderRepository) -> None:
        self._repo = repo

    def execute(self, po_number: str) -> PurchaseOrder:
        po = self._repo.get_by_po_number(po_number)
        if po is None:
            raise NotFound("PurchaseOrder", po_number)
        return po


class _POTransitionUseCase:
    """Every transition follows the same shape: fetch by po_number, apply
    the pure domain transition, stamp changed_at (docs/04's changed_since
    polling fallback), persist. Subclasses only supply the transition
    function; acknowledge overrides execute() because it also needs `now`
    passed into the transition itself."""

    _transition = staticmethod(lambda po: po)

    def __init__(self, repo: PurchaseOrderRepository, clock: ClockPort) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, po_number: str) -> PurchaseOrder:
        po = self._repo.get_by_po_number(po_number)
        if po is None:
            raise NotFound("PurchaseOrder", po_number)
        updated = self._transition(po)
        updated = replace(updated, changed_at=self._clock.now())
        return self._repo.update(updated)


class SubmitPurchaseOrderForApproval(_POTransitionUseCase):
    _transition = staticmethod(txn.submit_for_approval)


class ApprovePurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.approve)


class RejectPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.reject)


class WithdrawPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.withdraw)


class CancelPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.cancel)


class HoldPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.hold)


class ReleaseHoldPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.release_hold)


class AmendPurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.amend)


class ApprovePurchaseOrderAmendment(_POTransitionUseCase):
    _transition = staticmethod(txn.approve_amendment)


class ClosePurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.close)


class FinallyClosePurchaseOrder(_POTransitionUseCase):
    _transition = staticmethod(txn.finally_close)


class AcknowledgePurchaseOrder:
    def __init__(self, repo: PurchaseOrderRepository, clock: ClockPort) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, po_number: str) -> PurchaseOrder:
        po = self._repo.get_by_po_number(po_number)
        if po is None:
            raise NotFound("PurchaseOrder", po_number)
        now = self._clock.now()
        updated = txn.acknowledge(po, now)
        updated = replace(updated, changed_at=now)
        return self._repo.update(updated)
