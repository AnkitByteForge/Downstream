from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.vendor import Vendor, VendorScopeView
from domain.repositories.vendor_repository import VendorRepository, VendorScopeViewRepository
from infrastructure.persistence.orm_models import VendorModel, VendorScopeViewModel


def _vendor_to_domain(row: VendorModel) -> Vendor:
    return Vendor(
        id=row.id,
        name=row.name,
        qualification_status=row.qualification_status,
        performance_score=float(row.performance_score) if row.performance_score is not None else None,
    )


def _scope_view_to_domain(row: VendorScopeViewModel) -> VendorScopeView:
    return VendorScopeView(
        id=row.id,
        vendor_id=row.vendor_id,
        company_code=row.company_code,
        purchasing_org=row.purchasing_org,
        blocked=row.blocked,
        purchasing_terms=row.purchasing_terms or {},
    )


class SqlAlchemyVendorRepository(VendorRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, vendor: Vendor) -> Vendor:
        row = VendorModel(
            name=vendor.name,
            qualification_status=vendor.qualification_status,
            performance_score=vendor.performance_score,
        )
        self._session.add(row)
        self._session.flush()
        return _vendor_to_domain(row)

    def get(self, vendor_id: int) -> Vendor | None:
        row = self._session.get(VendorModel, vendor_id)
        return _vendor_to_domain(row) if row else None

    def list_all(self) -> list[Vendor]:
        rows = self._session.execute(select(VendorModel)).scalars().all()
        return [_vendor_to_domain(r) for r in rows]

    def update(self, vendor: Vendor) -> Vendor:
        row = self._session.get(VendorModel, vendor.id)
        assert row is not None
        row.qualification_status = vendor.qualification_status
        row.performance_score = vendor.performance_score
        self._session.flush()
        return _vendor_to_domain(row)


class SqlAlchemyVendorScopeViewRepository(VendorScopeViewRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, scope_view: VendorScopeView) -> VendorScopeView:
        row = VendorScopeViewModel(
            vendor_id=scope_view.vendor_id,
            company_code=scope_view.company_code,
            purchasing_org=scope_view.purchasing_org,
            blocked=scope_view.blocked,
            purchasing_terms=scope_view.purchasing_terms,
        )
        self._session.add(row)
        self._session.flush()
        return _scope_view_to_domain(row)

    def list_by_vendor(self, vendor_id: int) -> list[VendorScopeView]:
        rows = (
            self._session.execute(
                select(VendorScopeViewModel).where(VendorScopeViewModel.vendor_id == vendor_id)
            )
            .scalars()
            .all()
        )
        return [_scope_view_to_domain(r) for r in rows]
