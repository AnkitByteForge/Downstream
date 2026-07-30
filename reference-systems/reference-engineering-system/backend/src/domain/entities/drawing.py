from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from domain.value_objects import RevisionCloud

DRAWING_VERSION_STATUSES = ("DRAFT", "ISSUED", "REVISED", "SUPERSEDED")


@dataclass
class Drawing:
    """A sheet, identified by discipline sheet number (e.g. A-101). Owns a
    pointer to whichever version is current."""

    id: int | None
    project_id: int
    sheet_number: str
    title: str
    discipline_code: str
    current_version_id: int | None = None


@dataclass
class DrawingVersion:
    """One issuance of a Drawing. Current-version-by-issuance-date and explicit
    supersession (Reference Engineering System doc §4/§7) — superseded_by_id is
    the pointer the engine must never reason off a stale sheet without checking.
    """

    id: int | None
    drawing_id: int
    revision_label: str  # "Rev A" (pre-IFC) or "Rev 0", "Rev 1"... (post-IFC)
    issuance_date: date
    status: str
    discipline_code: str
    superseded_by_id: int | None = None
    revision_clouds: list[RevisionCloud] = field(default_factory=list)
    location_ids: list[int] = field(default_factory=list)
