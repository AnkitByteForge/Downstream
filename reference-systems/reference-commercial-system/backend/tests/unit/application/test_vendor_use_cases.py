from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.vendor_use_cases import (
    AddVendorScopeView,
    ApproveVendor,
    CreateVendor,
    GetVendor,
    ListVendors,
    ListVendorScopeViews,
    PrequalifyVendor,
)
from domain.exceptions import InvalidTransition

from tests.unit.application.fakes import InMemoryVendorRepository, InMemoryVendorScopeViewRepository


def test_create_and_get_vendor() -> None:
    repo = InMemoryVendorRepository()
    created = CreateVendor(repo).execute("Voltrex Switchgear Inc.")
    fetched = GetVendor(repo).execute(created.id)
    assert fetched.name == "Voltrex Switchgear Inc."
    assert fetched.qualification_status == "PROSPECTIVE"


def test_get_vendor_not_found() -> None:
    repo = InMemoryVendorRepository()
    with pytest.raises(NotFound):
        GetVendor(repo).execute(999)


def test_list_vendors() -> None:
    repo = InMemoryVendorRepository()
    CreateVendor(repo).execute("A")
    CreateVendor(repo).execute("B")
    assert len(ListVendors(repo).execute()) == 2


def test_prequalify_then_approve_vendor() -> None:
    repo = InMemoryVendorRepository()
    v = CreateVendor(repo).execute("A")
    v = PrequalifyVendor(repo).execute(v.id)
    v = ApproveVendor(repo).execute(v.id)
    assert v.qualification_status == "APPROVED"


def test_approve_vendor_before_prequalify_raises() -> None:
    repo = InMemoryVendorRepository()
    v = CreateVendor(repo).execute("A")
    with pytest.raises(InvalidTransition):
        ApproveVendor(repo).execute(v.id)


def test_prequalify_not_found() -> None:
    repo = InMemoryVendorRepository()
    with pytest.raises(NotFound):
        PrequalifyVendor(repo).execute(999)


def test_add_and_list_vendor_scope_views() -> None:
    vendor_repo = InMemoryVendorRepository()
    scope_repo = InMemoryVendorScopeViewRepository()
    v = CreateVendor(vendor_repo).execute("A")
    AddVendorScopeView(scope_repo).execute(v.id, company_code="1000", purchasing_org="PORG1")
    AddVendorScopeView(scope_repo).execute(v.id, company_code="2000", purchasing_org="PORG2", blocked=True)
    views = ListVendorScopeViews(scope_repo).execute(v.id)
    assert len(views) == 2
    assert {sv.company_code for sv in views} == {"1000", "2000"}
    assert any(sv.blocked for sv in views)
