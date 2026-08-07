from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.exceptions import DomainError
from domain.value_objects import BallInCourt

# Closed engineering-authorization "enums" (same convention as RFI_STATUSES /
# DRAWING_VERSION_STATUSES — ADR-003 calls these closed Python-level enums,
# realized here as string vocabularies on a str field). The Design Change
# family is a single entity whose type distinguishes the authority instrument,
# not three separate entity classes (ADR-007).
DESIGN_CHANGE_TYPES = ("ASI", "CCD", "BULLETIN")
DESIGN_CHANGE_STATUSES = ("DRAFT", "ISSUED", "ACKNOWLEDGED", "SUPERSEDED", "VOID")


@dataclass
class DesignChange:
    """An engineering-authorization instrument (ADR-007).

    One closed type enum (ASI / CCD / BULLETIN) distinguishes the authority
    level of the instrument; one lifecycle (DRAFT -> ISSUED -> ACKNOWLEDGED,
    with SUPERSEDED / VOID as non-forward terminal states) tracks its
    engineering-authorization state only. Drawing incorporation is expressed
    through relationships to affected DrawingVersion(s) — it is NOT collapsed
    into the DesignChange state itself. Pricing / settlement (ChangeEvent,
    PCO, COR, ChangeOrder) are explicitly out of the Reference Engineering
    System's scope and belong to the future Reference Commercial System.

    The originating RFI is nullable because a DesignChange may be issued
    directly without an RFI. id is the opaque real primary key; display_number
    is the separate, editable, human-facing label (e.g. "ASI-07"), never a key
    (docs/04 point 5).
    """

    id: int | None
    project_id: int
    number: str
    display_number: str
    type: str  # DESIGN_CHANGE_TYPES
    status: str = "DRAFT"  # DESIGN_CHANGE_STATUSES
    change_reason: str | None = None
    discipline_code: str | None = None
    source_rfi_id: int | None = None
    ball_in_court: BallInCourt = field(default_factory=lambda: BallInCourt("architect", None))
    affected_drawing_version_ids: list[int] = field(default_factory=list)
    affected_spec_section_ids: list[int] = field(default_factory=list)
    location_ids: list[int] = field(default_factory=list)
    superseded_by_id: int | None = None
    issued_at: datetime | None = None
    acknowledged_at: datetime | None = None
    voided_at: datetime | None = None

    def __post_init__(self) -> None:
        """Domain invariant: type and status must come from their closed
        vocabularies. Guards structural creation of an instrument the state
        machine and RES would never recognize (e.g. a Commercial "ChangeOrder"
        or a pricing "PRICED" state)."""
        if self.type not in DESIGN_CHANGE_TYPES:
            raise DomainError(f"Invalid DesignChange type: {self.type!r}")
        if self.status not in DESIGN_CHANGE_STATUSES:
            raise DomainError(f"Invalid DesignChange status: {self.status!r}")
