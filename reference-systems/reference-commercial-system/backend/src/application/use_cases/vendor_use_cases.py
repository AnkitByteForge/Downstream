from __future__ import annotations

from domain.entities.vendor import Vendor, VendorScopeView
from domain.repositories.vendor_repository import VendorRepository, VendorScopeViewRepository
from domain.state_machines import vendor_transitions

from application.exceptions import NotFound


class CreateVendor:
    def __init__(self, repo: VendorRepository) -> None:
        self._repo = repo

    def execute(self, name: str) -> Vendor:
        return self._repo.add(Vendor(id=None, name=name))


class ListVendors:
    def __init__(self, repo: VendorRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Vendor]:
        return self._repo.list_all()


class GetVendor:
    def __init__(self, repo: VendorRepository) -> None:
        self._repo = repo

    def execute(self, vendor_id: int) -> Vendor:
        vendor = self._repo.get(vendor_id)
        if vendor is None:
            raise NotFound("Vendor", vendor_id)
        return vendor


class _VendorTransitionUseCase:
    _transition = staticmethod(lambda v: v)

    def __init__(self, repo: VendorRepository) -> None:
        self._repo = repo

    def execute(self, vendor_id: int) -> Vendor:
        vendor = self._repo.get(vendor_id)
        if vendor is None:
            raise NotFound("Vendor", vendor_id)
        updated = self._transition(vendor)
        return self._repo.update(updated)


class PrequalifyVendor(_VendorTransitionUseCase):
    _transition = staticmethod(vendor_transitions.prequalify)


class ApproveVendor(_VendorTransitionUseCase):
    _transition = staticmethod(vendor_transitions.approve)


class SuspendVendor(_VendorTransitionUseCase):
    _transition = staticmethod(vendor_transitions.suspend)


class BlacklistVendor(_VendorTransitionUseCase):
    _transition = staticmethod(vendor_transitions.blacklist)


class AddVendorScopeView:
    def __init__(self, repo: VendorScopeViewRepository) -> None:
        self._repo = repo

    def execute(
        self,
        vendor_id: int,
        company_code: str | None,
        purchasing_org: str | None,
        blocked: bool = False,
    ) -> VendorScopeView:
        return self._repo.add(
            VendorScopeView(
                id=None,
                vendor_id=vendor_id,
                company_code=company_code,
                purchasing_org=purchasing_org,
                blocked=blocked,
            )
        )


class ListVendorScopeViews:
    def __init__(self, repo: VendorScopeViewRepository) -> None:
        self._repo = repo

    def execute(self, vendor_id: int) -> list[VendorScopeView]:
        return self._repo.list_by_vendor(vendor_id)
