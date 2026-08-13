from __future__ import annotations

from domain.entities.commitment import Commitment
from domain.repositories.commitment_repository import CommitmentRepository
from domain.state_machines import commitment_transitions
from domain.value_objects import OrgScope

from application.exceptions import NotFound


class CreateCommitment:
    def __init__(self, repo: CommitmentRepository) -> None:
        self._repo = repo

    def execute(
        self,
        source_type: str,
        cost_code_id: int,
        committed_amount: float,
        currency: str,
        po_id: int | None = None,
        org_scope: OrgScope | None = None,
    ) -> Commitment:
        return self._repo.add(
            Commitment(
                id=None,
                source_type=source_type,
                cost_code_id=cost_code_id,
                committed_amount=committed_amount,
                currency=currency,
                po_id=po_id,
                org_scope=org_scope or OrgScope(),
            )
        )


class ListCommitments:
    def __init__(self, repo: CommitmentRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Commitment]:
        return self._repo.list_all()


class GetCommitment:
    def __init__(self, repo: CommitmentRepository) -> None:
        self._repo = repo

    def execute(self, commitment_id: int) -> Commitment:
        commitment = self._repo.get(commitment_id)
        if commitment is None:
            raise NotFound("Commitment", commitment_id)
        return commitment


class RelieveCommitment:
    def __init__(self, repo: CommitmentRepository) -> None:
        self._repo = repo

    def execute(self, commitment_id: int, amount: float) -> Commitment:
        commitment = self._repo.get(commitment_id)
        if commitment is None:
            raise NotFound("Commitment", commitment_id)
        updated = commitment_transitions.relieve(commitment, amount)
        return self._repo.update(updated)


class CancelCommitment:
    def __init__(self, repo: CommitmentRepository) -> None:
        self._repo = repo

    def execute(self, commitment_id: int) -> Commitment:
        commitment = self._repo.get(commitment_id)
        if commitment is None:
            raise NotFound("Commitment", commitment_id)
        updated = commitment_transitions.cancel(commitment)
        return self._repo.update(updated)
