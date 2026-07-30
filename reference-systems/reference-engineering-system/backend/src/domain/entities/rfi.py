from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.value_objects import BallInCourt

RFI_STATUSES = ("DRAFT", "OPEN", "RESPONDED", "CLOSED")


@dataclass
class RFI:
    """Request for Information — contractor -> A/E clarification request
    (Reference Engineering System doc §5). Ball-in-court routing is the
    backbone of its workflow: Draft -> Open(BIC=assignee) -> Responded
    (BIC=manager) -> Closed.

    id is the opaque, real primary key; display_number is the separate,
    editable, human-facing label (docs/04 point 5) — never used as a key.
    """

    id: int | None
    project_id: int
    number: str
    display_number: str
    subject: str
    ball_in_court: BallInCourt
    status: str = "DRAFT"
    question: str | None = None
    response: str | None = None
    cost_impact_flag: str | None = None  # "YES" | "YES_UNKNOWN" | "NO"
    cost_code: str | None = None
    discipline_code: str | None = None
    spawned_change_id: int | None = None
    raw_document_ref: str | None = None
    drawing_version_ids: list[int] = field(default_factory=list)
    spec_section_ids: list[int] = field(default_factory=list)
    location_ids: list[int] = field(default_factory=list)
    closed_at: datetime | None = None
