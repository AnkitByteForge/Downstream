from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import DomainError

# SYNCHRO's five native appearance-task behaviors (The Reference Engineering
# System.md §16 caveat): Install / Maintain / Neutral / Remove / Temporary.
APPEARANCE_PROFILES = ("INSTALL", "MAINTAIN", "NEUTRAL", "REMOVE", "TEMPORARY")


@dataclass
class ModelObject:
    """A BIM/3D coordination object (`The Reference Engineering System.md`
    §16), mirroring the SYNCHRO pattern where a 3D object links to a schedule
    task through a Resource intermediary carrying an appearance profile.
    `resource_link_id` collapses that intermediary into a single nullable
    pointer straight at `ScheduleActivity.id`, per the source doc's own
    caveat permitting the abstraction (ADR-008). Read-only reference data —
    no lifecycle."""

    id: int | None
    project_id: int
    discipline_code: str
    appearance_profile: str  # APPEARANCE_PROFILES
    location_id: int | None = None
    resource_link_id: int | None = None

    def __post_init__(self) -> None:
        if self.appearance_profile not in APPEARANCE_PROFILES:
            raise DomainError(f"Invalid ModelObject appearance_profile: {self.appearance_profile!r}")
