from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BallInCourt:
    """Who must act next on an RFI or Submittal, per the real ball-in-court routing
    mechanic (Reference Engineering System doc §5): creating an RFI as Open shifts
    ball-in-court to the assignee; on response it returns to the manager (typically GC).
    """

    party_role: str  # e.g. "assignee" | "manager" | "subcontractor" | "gc" | "architect"
    user_id: int | None = None

    def __str__(self) -> str:
        return self.party_role
