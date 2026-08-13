from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.cost_code import CostCode


class CostCodeRepository(ABC):
    @abstractmethod
    def add(self, cost_code: CostCode) -> CostCode: ...

    @abstractmethod
    def get(self, cost_code_id: int) -> CostCode | None: ...

    @abstractmethod
    def get_by_native_code(self, native_code: str) -> CostCode | None: ...

    @abstractmethod
    def list_all(self) -> list[CostCode]: ...
