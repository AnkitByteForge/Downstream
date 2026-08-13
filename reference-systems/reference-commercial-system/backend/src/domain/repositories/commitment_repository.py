from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.commitment import Commitment


class CommitmentRepository(ABC):
    @abstractmethod
    def add(self, commitment: Commitment) -> Commitment: ...

    @abstractmethod
    def get(self, commitment_id: int) -> Commitment | None: ...

    @abstractmethod
    def list_all(self) -> list[Commitment]: ...

    @abstractmethod
    def update(self, commitment: Commitment) -> Commitment: ...
