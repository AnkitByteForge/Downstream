from __future__ import annotations

from dataclasses import replace

from domain.entities.commitment import Commitment
from domain.exceptions import DomainRuleViolation, InvalidTransition

# The Reference Commercial System.md §M item 4:
# Open -> Partially Relieved -> Fully Relieved, or Open/Partially Relieved -> Cancelled.


def relieve(commitment: Commitment, amount: float) -> Commitment:
    if commitment.status not in ("OPEN", "PARTIALLY_RELIEVED"):
        raise InvalidTransition("Commitment", commitment.status, "relieved")
    if amount <= 0:
        raise DomainRuleViolation("Commitment relief amount must be positive")
    new_relieved = commitment.relieved_amount + amount
    if new_relieved > commitment.committed_amount:
        raise DomainRuleViolation("Commitment relief amount exceeds committed_amount")
    new_status = "FULLY_RELIEVED" if new_relieved >= commitment.committed_amount else "PARTIALLY_RELIEVED"
    return replace(commitment, relieved_amount=new_relieved, status=new_status)


def cancel(commitment: Commitment) -> Commitment:
    if commitment.status not in ("OPEN", "PARTIALLY_RELIEVED"):
        raise InvalidTransition("Commitment", commitment.status, "CANCELLED")
    return replace(commitment, status="CANCELLED")
