from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.contract import Contract


class ContractRepository(ABC):
    @abstractmethod
    def add(self, contract: Contract) -> Contract: ...

    @abstractmethod
    def get(self, contract_id: int) -> Contract | None: ...

    @abstractmethod
    def list_all(self) -> list[Contract]: ...
