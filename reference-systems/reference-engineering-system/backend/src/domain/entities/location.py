from __future__ import annotations

from dataclasses import dataclass

LOCATION_TYPES = ("site", "building", "level", "zone", "room", "gridline")


@dataclass
class Location:
    """One node in the project's recursive, unlimited-tier location tree
    (Reference Engineering System doc §12)."""

    id: int | None
    project_id: int
    parent_id: int | None
    tier_level: int
    name: str
    type: str
