from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.vendor import Commitment, Vendor


class VendorRepository(ABC):
    @abstractmethod
    def add(self, vendor: Vendor) -> Vendor: ...

    @abstractmethod
    def get(self, vendor_id: int) -> Vendor | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[Vendor]: ...


class CommitmentRepository(ABC):
    @abstractmethod
    def add(self, commitment: Commitment) -> Commitment: ...

    @abstractmethod
    def get(self, commitment_id: int) -> Commitment | None: ...
