from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from domain.entities.purchase_order import PurchaseOrder
from domain.exceptions import DomainRuleViolation, InvalidTransition

# PurchaseOrder header lifecycle (The Reference Commercial System.md §C),
# normalized per that document's own Caveats into:
#   DRAFT -> PENDING_APPROVAL -> OPEN -> [ON_HOLD <-> OPEN]
#         -> [PENDING_CHANGE_APPROVAL -> OPEN] -> CLOSED -> FINALLY_CLOSED
#   terminal side-branches from DRAFT/PENDING_APPROVAL: CANCELED, REJECTED, WITHDRAWN
# acknowledged/delivery_completed/final_invoice are boolean flags (SAP's own
# indicator model — ELIKZ etc.), not separate statuses.


def submit_for_approval(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "DRAFT":
        raise InvalidTransition("PurchaseOrder", po.status, "PENDING_APPROVAL")
    return replace(po, status="PENDING_APPROVAL")


def approve(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "PENDING_APPROVAL":
        raise InvalidTransition("PurchaseOrder", po.status, "OPEN")
    return replace(po, status="OPEN")


def reject(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "PENDING_APPROVAL":
        raise InvalidTransition("PurchaseOrder", po.status, "REJECTED")
    return replace(po, status="REJECTED")


def withdraw(po: PurchaseOrder) -> PurchaseOrder:
    if po.status not in ("DRAFT", "PENDING_APPROVAL"):
        raise InvalidTransition("PurchaseOrder", po.status, "WITHDRAWN")
    return replace(po, status="WITHDRAWN")


def cancel(po: PurchaseOrder) -> PurchaseOrder:
    if po.status not in ("DRAFT", "PENDING_APPROVAL", "OPEN"):
        raise InvalidTransition("PurchaseOrder", po.status, "CANCELED")
    return replace(po, status="CANCELED")


def acknowledge(po: PurchaseOrder, now: datetime) -> PurchaseOrder:
    if po.status != "OPEN":
        raise InvalidTransition("PurchaseOrder", po.status, "OPEN(acknowledged)")
    if po.acknowledged:
        raise DomainRuleViolation("PurchaseOrder is already acknowledged")
    return replace(po, acknowledged=True, acknowledged_at=now)


def hold(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "OPEN":
        raise InvalidTransition("PurchaseOrder", po.status, "ON_HOLD")
    return replace(po, status="ON_HOLD")


def release_hold(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "ON_HOLD":
        raise InvalidTransition("PurchaseOrder", po.status, "OPEN")
    return replace(po, status="OPEN")


def amend(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "OPEN":
        raise InvalidTransition("PurchaseOrder", po.status, "PENDING_CHANGE_APPROVAL")
    return replace(po, status="PENDING_CHANGE_APPROVAL")


def approve_amendment(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "PENDING_CHANGE_APPROVAL":
        raise InvalidTransition("PurchaseOrder", po.status, "OPEN")
    return replace(po, status="OPEN")


def close(po: PurchaseOrder) -> PurchaseOrder:
    if po.status not in ("OPEN", "ON_HOLD"):
        raise InvalidTransition("PurchaseOrder", po.status, "CLOSED")
    return replace(po, status="CLOSED", delivery_completed=True, final_invoice=True)


def finally_close(po: PurchaseOrder) -> PurchaseOrder:
    if po.status != "CLOSED":
        raise InvalidTransition("PurchaseOrder", po.status, "FINALLY_CLOSED")
    return replace(po, status="FINALLY_CLOSED")
