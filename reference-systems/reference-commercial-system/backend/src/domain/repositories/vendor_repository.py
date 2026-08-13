from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.vendor import Vendor, VendorScopeView


class VendorRepository(ABC):
    @abstractmethod
    def add(self, vendor: Vendor) -> Vendor: ...

    @abstractmethod
    def get(self, vendor_id: int) -> Vendor | None: ...

    @abstractmethod
    def list_all(self) -> list[Vendor]: ...

    @abstractmethod
    def update(self, vendor: Vendor) -> Vendor: ...


class VendorScopeViewRepository(ABC):
    @abstractmethod
    def add(self, scope_view: VendorScopeView) -> VendorScopeView: ...

    @abstractmethod
    def list_by_vendor(self, vendor_id: int) -> list[VendorScopeView]: ...
