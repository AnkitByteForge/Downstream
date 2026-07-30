from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import RFI


class RFIRepository(ABC):
    @abstractmethod
    def get(self, rfi_id: int) -> RFI | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[RFI]: ...

    @abstractmethod
    def add(self, rfi: RFI) -> RFI: ...

    @abstractmethod
    def update(self, rfi: RFI) -> RFI: ...
