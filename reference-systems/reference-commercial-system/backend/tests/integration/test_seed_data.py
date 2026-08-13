from __future__ import annotations

from seed.meridian_tower_commercial import seed
from infrastructure.persistence.repositories.sqlalchemy_commitment_repository import (
    SqlAlchemyCommitmentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_purchase_order_repository import (
    SqlAlchemyPOLineRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import SqlAlchemyVendorRepository


def test_canonical_seed_reproduces_scenario_a_and_b_exactly(db_session):
    """Seeds the canonical dataset inside a rolled-back transaction and
    asserts the resulting shape matches Canonical_Demo_Dataset.md §9-10
    exactly — proving the seed is idempotent-in-spirit and future-proof,
    mirroring the Reference Engineering System's own seed assertion test.
    """
    result = seed(db_session)
    assert result["scenario_a_pos"] == ["4500018823", None, "4500019104"]
    assert result["scenario_b_pos"] == ["4500020045", "4500020091"]

    vendor_repo = SqlAlchemyVendorRepository(db_session)
    vendor_names = {v.name for v in vendor_repo.list_all()}
    assert vendor_names == {
        "VendorCo Metals",
        "Arjun Steelworks",
        "ThermaWrap",
        "Voltrex Switchgear Inc.",
        "Ferro Electrical Supply",
    }
    assert all(v.qualification_status == "APPROVED" for v in vendor_repo.list_all())

    po_repo = SqlAlchemyPurchaseOrderRepository(db_session)
    all_pos = po_repo.list_all()
    assert len(all_pos) == 5  # exactly po_4471/4488/4512/5201/5202 — req_5203 deferred, ADR-017

    po_4471 = po_repo.get_by_po_number("4500018823")
    assert po_4471.currency == "INR"
    assert po_4471.org_scope.company_code == "1000"
    assert po_4471.status == "OPEN"
    assert po_4471.acknowledged is True

    line_4471 = SqlAlchemyPOLineRepository(db_session).list_by_po(po_4471.id)[0]
    assert line_4471.value == 820000
    assert line_4471.lifecycle_position == "in_fabrication"
    assert line_4471.spec_section_refs == ["23 31 13"]

    po_4488 = next(po for po in all_pos if po.vendor_id == _vendor_id(vendor_repo, "Arjun Steelworks"))
    assert po_4488.po_number is None  # docs/05: "not stated in trace" — ADR-017
    line_4488 = SqlAlchemyPOLineRepository(db_session).list_by_po(po_4488.id)[0]
    assert line_4488.value == 610000
    assert line_4488.lifecycle_position == "shipped"
    assert line_4488.cost_code_id is None  # no cost code stated in docs/05

    po_4512 = po_repo.get_by_po_number("4500019104")
    line_4512 = SqlAlchemyPOLineRepository(db_session).list_by_po(po_4512.id)[0]
    assert line_4512.value == 410000
    assert line_4512.lifecycle_position == "issued"  # SCHEDULED, not yet in_fabrication

    po_5201 = po_repo.get_by_po_number("4500020045")
    assert po_5201.currency == "USD"
    assert po_5201.org_scope.company_code == "2000"
    line_5201 = SqlAlchemyPOLineRepository(db_session).list_by_po(po_5201.id)[0]
    assert line_5201.value == 42000000
    assert line_5201.lifecycle_position == "in_fabrication"

    po_5202 = po_repo.get_by_po_number("4500020091")
    assert po_5202.currency == "USD"
    line_5202 = SqlAlchemyPOLineRepository(db_session).list_by_po(po_5202.id)[0]
    assert line_5202.value == 6500000
    assert line_5202.lifecycle_position == "shipped"

    cost_code_repo = SqlAlchemyCostCodeRepository(db_session)
    cost_codes = cost_code_repo.list_all()
    assert len(cost_codes) == 2
    assert {c.native_code for c in cost_codes} == {"23-100", "26-200"}

    commitment_repo = SqlAlchemyCommitmentRepository(db_session)
    commitments = commitment_repo.list_all()
    assert len(commitments) == 3  # po_4471, po_5201, po_5202 only — ADR-015
    committed_amounts = {c.committed_amount for c in commitments}
    assert committed_amounts == {820000, 42000000, 6500000}

    # Never aggregate INR and USD together (ADR-016) — the two currencies
    # never collapse into a single project-wide total anywhere in this seed.
    currencies = {c.currency for c in commitments}
    assert currencies == {"INR", "USD"}


def _vendor_id(vendor_repo, name: str) -> int:
    return next(v.id for v in vendor_repo.list_all() if v.name == name)
