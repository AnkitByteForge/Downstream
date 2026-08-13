from __future__ import annotations

import pytest

from domain.entities.commitment import Commitment
from domain.entities.contract import Contract
from domain.entities.cost_code import CostCode
from domain.entities.purchase_order import POLine, POScheduleLine, PurchaseOrder
from domain.entities.vendor import Vendor
from domain.exceptions import DomainRuleViolation


def test_vendor_rejects_invalid_qualification_status() -> None:
    with pytest.raises(DomainRuleViolation):
        Vendor(id=1, name="X", qualification_status="NOT_A_STATUS")


def test_cost_code_rejects_invalid_format() -> None:
    with pytest.raises(DomainRuleViolation):
        CostCode(id=1, native_code="23-100", cost_code_format="NOT_A_FORMAT")


def test_cost_code_accepts_every_documented_format() -> None:
    for fmt in ("CSI_MASTERFORMAT", "SAP_WBS", "ORACLE_PROJECT_TASK", "ERPNEXT_COST_CENTER", "CUSTOM"):
        CostCode(id=1, native_code="X", cost_code_format=fmt)


def test_contract_rejects_invalid_type() -> None:
    with pytest.raises(DomainRuleViolation):
        Contract(id=1, vendor_id=1, type="NOT_A_TYPE")


def test_contract_accepts_every_documented_type() -> None:
    for t in ("BLANKET", "SCHEDULING_AGREEMENT", "SUBCONTRACT"):
        Contract(id=1, vendor_id=1, type=t)


def test_commitment_rejects_invalid_source_type() -> None:
    with pytest.raises(DomainRuleViolation):
        Commitment(id=1, source_type="NOT_A_SOURCE", cost_code_id=1, committed_amount=100, currency="USD")


def test_commitment_rejects_invalid_status() -> None:
    with pytest.raises(DomainRuleViolation):
        Commitment(
            id=1, source_type="PO", cost_code_id=1, committed_amount=100, currency="USD", status="BOGUS"
        )


def test_commitment_open_amount_computed() -> None:
    c = Commitment(
        id=1, source_type="PO", cost_code_id=1, committed_amount=1000, currency="USD", relieved_amount=300
    )
    assert c.open_amount == 700


def test_purchase_order_rejects_invalid_status() -> None:
    with pytest.raises(DomainRuleViolation):
        PurchaseOrder(id=1, po_number="1", vendor_id=1, currency="USD", status="NOT_A_STATUS")


def test_po_line_rejects_invalid_lifecycle_position() -> None:
    with pytest.raises(DomainRuleViolation):
        POLine(
            id=1,
            po_id=1,
            line_no=1,
            description="X",
            quantity=1,
            uom="EA",
            unit_price=1,
            value=1,
            lifecycle_position="NOT_A_STAGE",
        )


def test_po_line_accepts_every_documented_lifecycle_position() -> None:
    for stage in ("draft", "issued", "in_fabrication", "shipped", "installed"):
        POLine(
            id=1,
            po_id=1,
            line_no=1,
            description="X",
            quantity=1,
            uom="EA",
            unit_price=1,
            value=1,
            lifecycle_position=stage,
        )


def test_po_schedule_line_rejects_invalid_delivery_status() -> None:
    with pytest.raises(DomainRuleViolation):
        POScheduleLine(id=1, po_line_id=1, schedule_no=1, quantity=1, delivery_status="NOT_A_STATUS")


def test_po_schedule_line_accepts_every_documented_delivery_status() -> None:
    for status in ("SCHEDULED", "CONFIRMED_ASN", "IN_TRANSIT", "PARTIALLY_DELIVERED", "DELIVERED"):
        POScheduleLine(id=1, po_line_id=1, schedule_no=1, quantity=1, delivery_status=status)
