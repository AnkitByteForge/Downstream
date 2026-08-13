from __future__ import annotations

from datetime import date, datetime, timezone

from domain.entities.commitment import Commitment
from domain.entities.purchase_order import POLine, POScheduleLine, PurchaseOrder
from domain.entities.vendor import Vendor
from domain.value_objects import OrgScope
from infrastructure.persistence.repositories.sqlalchemy_commitment_repository import (
    SqlAlchemyCommitmentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_purchase_order_repository import (
    SqlAlchemyPOLineRepository,
    SqlAlchemyPOScheduleLineRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import SqlAlchemyVendorRepository
from domain.entities.cost_code import CostCode


def _vendor(db_session, name="Test Vendor"):
    return SqlAlchemyVendorRepository(db_session).add(Vendor(id=None, name=name))


def test_purchase_order_round_trips_with_nullable_po_number(db_session) -> None:
    """Grounds ADR-017: PO-4488's own SAP number is "not stated in trace" —
    po_number must be able to stay None through a real round trip."""
    repo = SqlAlchemyPurchaseOrderRepository(db_session)
    vendor = _vendor(db_session, "Arjun Steelworks")
    created = repo.add(
        PurchaseOrder(
            id=None,
            po_number=None,
            vendor_id=vendor.id,
            currency="INR",
            org_scope=OrgScope(company_code="1000", plant="P100"),
        )
    )
    fetched = repo.get(created.id)
    assert fetched.po_number is None
    assert fetched.org_scope.company_code == "1000"

    # A number distinct from every canonical seed PO (which is committed
    # permanently, unlike this rollback-isolated fixture row).
    by_number = repo.get_by_po_number("INTEGRATION-TEST-PO-NONEXISTENT")
    assert by_number is None  # no such PO created in this test


def test_purchase_order_get_by_po_number(db_session) -> None:
    repo = SqlAlchemyPurchaseOrderRepository(db_session)
    vendor = _vendor(db_session)
    repo.add(
        PurchaseOrder(
            id=None,
            po_number="INTEGRATION-TEST-PO-1",
            vendor_id=vendor.id,
            currency="INR",
            org_scope=OrgScope(),
        )
    )
    found = repo.get_by_po_number("INTEGRATION-TEST-PO-1")
    assert found is not None
    assert found.currency == "INR"


def test_purchase_order_changed_since_filter(db_session) -> None:
    repo = SqlAlchemyPurchaseOrderRepository(db_session)
    vendor = _vendor(db_session)
    po = repo.add(
        PurchaseOrder(id=None, po_number="PO-X", vendor_id=vendor.id, currency="USD", org_scope=OrgScope())
    )
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert repo.list_changed_since(cutoff) == []

    stamped = repo.update(PurchaseOrder(**{**vars(po), "changed_at": datetime(2026, 7, 30, tzinfo=timezone.utc)}))
    results = repo.list_changed_since(cutoff)
    assert len(results) == 1
    assert results[0].id == stamped.id


def test_po_line_round_trips_with_nullable_cost_code_and_spec_refs(db_session) -> None:
    po_repo = SqlAlchemyPurchaseOrderRepository(db_session)
    line_repo = SqlAlchemyPOLineRepository(db_session)
    vendor = _vendor(db_session)
    po = po_repo.add(
        PurchaseOrder(id=None, po_number="PO-Y", vendor_id=vendor.id, currency="USD", org_scope=OrgScope())
    )
    line = line_repo.add(
        POLine(
            id=None,
            po_id=po.id,
            line_no=1,
            description="Switchgear lineup",
            quantity=1,
            uom="LOT",
            unit_price=42000000,
            value=42000000,
            spec_section_refs=["26 24 13"],
            lifecycle_position="in_fabrication",
        )
    )
    fetched = line_repo.get(line.id)
    assert fetched.cost_code_id is None
    assert fetched.spec_section_refs == ["26 24 13"]
    assert fetched.lifecycle_position == "in_fabrication"

    by_po = line_repo.list_by_po(po.id)
    assert len(by_po) == 1


def test_po_schedule_line_round_trips_with_external_business_key(db_session) -> None:
    """ADR-011: linked_schedule_activity_ref is a plain string business key
    into the Reference Engineering System, never a foreign key."""
    po_repo = SqlAlchemyPurchaseOrderRepository(db_session)
    line_repo = SqlAlchemyPOLineRepository(db_session)
    schedule_repo = SqlAlchemyPOScheduleLineRepository(db_session)
    vendor = _vendor(db_session)
    po = po_repo.add(
        PurchaseOrder(id=None, po_number="PO-Z", vendor_id=vendor.id, currency="USD", org_scope=OrgScope())
    )
    line = line_repo.add(
        POLine(
            id=None, po_id=po.id, line_no=1, description="X", quantity=1, uom="EA", unit_price=1, value=1
        )
    )
    schedule_line = schedule_repo.add(
        POScheduleLine(
            id=None,
            po_line_id=line.id,
            schedule_no=1,
            quantity=1,
            required_on_site_date=date(2027, 5, 15),
            linked_schedule_activity_ref="3410",
        )
    )
    fetched = schedule_repo.get(schedule_line.id)
    assert fetched.linked_schedule_activity_ref == "3410"
    assert fetched.required_on_site_date == date(2027, 5, 15)

    by_line = schedule_repo.list_by_po_line(line.id)
    assert len(by_line) == 1


def test_commitment_round_trips_and_relieves(db_session) -> None:
    cost_code_repo = SqlAlchemyCostCodeRepository(db_session)
    commitment_repo = SqlAlchemyCommitmentRepository(db_session)
    cost_code = cost_code_repo.add(CostCode(id=None, native_code="26-200", cost_code_format="CSI_MASTERFORMAT"))
    created = commitment_repo.add(
        Commitment(
            id=None,
            source_type="PO",
            cost_code_id=cost_code.id,
            committed_amount=42000000,
            currency="USD",
            org_scope=OrgScope(company_code="2000"),
        )
    )
    fetched = commitment_repo.get(created.id)
    assert fetched.status == "OPEN"
    assert fetched.open_amount == 42000000

    updated = commitment_repo.update(
        Commitment(**{**vars(fetched), "relieved_amount": 42000000, "status": "FULLY_RELIEVED"})
    )
    assert updated.open_amount == 0
