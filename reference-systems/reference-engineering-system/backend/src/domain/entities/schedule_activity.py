from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.exceptions import DomainError

# Closed vocabulary, same convention as DESIGN_CHANGE_TYPES / DRAWING_VERSION_STATUSES.
SCHEDULE_ACTIVITY_TYPES = ("TASK", "MILESTONE", "PROCUREMENT")


@dataclass
class ScheduleActivity:
    """A Primavera/Oracle-Contract-Management-shaped schedule activity
    (`The Reference Engineering System.md` §16). Read-only reference data —
    no status/lifecycle field (ADR-008): the "Submittal -> Approval -> PO ->
    Fabrication -> Delivery" procurement chain §16 describes is a chain across
    entities, expressed here as a relationship (`linked_submittal_ids`), not
    collapsed into an entity-local state.

    `wbs` is nullable because the one frozen seed instance (`sched_3410`,
    Canonical_Demo_Dataset.md §10/§13) specifies none (ADR-008).
    """

    id: int | None
    project_id: int
    activity_code: str
    type: str  # SCHEDULE_ACTIVITY_TYPES
    wbs: str | None = None
    predecessor_ids: list[int] = field(default_factory=list)
    successor_ids: list[int] = field(default_factory=list)
    linked_submittal_ids: list[int] = field(default_factory=list)
    delivery_milestone: datetime | None = None

    def __post_init__(self) -> None:
        if self.type not in SCHEDULE_ACTIVITY_TYPES:
            raise DomainError(f"Invalid ScheduleActivity type: {self.type!r}")
