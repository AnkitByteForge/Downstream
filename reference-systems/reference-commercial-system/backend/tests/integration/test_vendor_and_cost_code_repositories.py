from __future__ import annotations

from domain.entities.cost_code import CostCode
from domain.entities.vendor import Vendor, VendorScopeView
from domain.value_objects import OrgScope
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import (
    SqlAlchemyVendorRepository,
    SqlAlchemyVendorScopeViewRepository,
)


def test_vendor_round_trips_through_real_database(db_session) -> None:
    repo = SqlAlchemyVendorRepository(db_session)
    created = repo.add(Vendor(id=None, name="Voltrex Switchgear Inc.", performance_score=87.5))
    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.name == "Voltrex Switchgear Inc."
    assert fetched.qualification_status == "PROSPECTIVE"
    assert fetched.performance_score == 87.5


def test_vendor_qualification_status_update_persists(db_session) -> None:
    repo = SqlAlchemyVendorRepository(db_session)
    v = repo.add(Vendor(id=None, name="Ferro Electrical Supply"))
    v = repo.update(Vendor(**{**vars(v), "qualification_status": "APPROVED"}))
    refetched = repo.get(v.id)
    assert refetched.qualification_status == "APPROVED"


def test_vendor_scope_view_round_trips_with_blocked_flag(db_session) -> None:
    vendor_repo = SqlAlchemyVendorRepository(db_session)
    scope_repo = SqlAlchemyVendorScopeViewRepository(db_session)
    v = vendor_repo.add(Vendor(id=None, name="Arjun Steelworks"))
    scope_repo.add(
        VendorScopeView(id=None, vendor_id=v.id, company_code="1000", purchasing_org="PORG1", blocked=False)
    )
    scope_repo.add(
        VendorScopeView(
            id=None, vendor_id=v.id, company_code="2000", purchasing_org="PORG2", blocked=True
        )
    )
    views = scope_repo.list_by_vendor(v.id)
    assert len(views) == 2
    blocked_view = next(sv for sv in views if sv.company_code == "2000")
    assert blocked_view.blocked is True


def test_cost_code_round_trips_with_org_scope_and_standard_ref(db_session) -> None:
    # native_code distinct from the canonical seed's own "23-100"/"26-200"
    # (committed permanently) — this exact collision crashed
    # get_by_native_code the first time this test ran; see the CS-1
    # completion report and the fix in SqlAlchemyCostCodeRepository.
    repo = SqlAlchemyCostCodeRepository(db_session)
    created = repo.add(
        CostCode(
            id=None,
            native_code="INTEGRATION-TEST-26-200",
            cost_code_format="CSI_MASTERFORMAT",
            standard_ref="26 24 13",
            org_scope=OrgScope(company_code="2000", plant="P200"),
        )
    )
    fetched = repo.get(created.id)
    assert fetched.standard_ref == "26 24 13"
    assert fetched.org_scope.company_code == "2000"
    assert fetched.org_scope.plant == "P200"

    by_native_code = repo.get_by_native_code("INTEGRATION-TEST-26-200")
    assert by_native_code.id == created.id


def test_get_by_native_code_does_not_crash_when_code_recurs_across_org_scopes(db_session) -> None:
    """A native_code is not asserted globally unique (ADR-012) — two cost
    codes under different company codes may legitimately share one. This
    must return a match, not raise MultipleResultsFound."""
    repo = SqlAlchemyCostCodeRepository(db_session)
    repo.add(
        CostCode(
            id=None,
            native_code="SHARED-CODE",
            cost_code_format="CUSTOM",
            org_scope=OrgScope(company_code="1000"),
        )
    )
    repo.add(
        CostCode(
            id=None,
            native_code="SHARED-CODE",
            cost_code_format="CUSTOM",
            org_scope=OrgScope(company_code="2000"),
        )
    )
    found = repo.get_by_native_code("SHARED-CODE")
    assert found is not None
    assert found.native_code == "SHARED-CODE"


def test_cost_code_with_no_standard_ref_stays_null(db_session) -> None:
    """Grounds ADR-017's nullable cost_code fidelity gap: not every cost
    code is required to carry a standard_ref."""
    repo = SqlAlchemyCostCodeRepository(db_session)
    created = repo.add(CostCode(id=None, native_code="MISC-1", cost_code_format="CUSTOM"))
    fetched = repo.get(created.id)
    assert fetched.standard_ref is None
