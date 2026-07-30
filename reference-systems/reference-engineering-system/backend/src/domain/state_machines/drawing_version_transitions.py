from __future__ import annotations

from dataclasses import replace

from domain.entities.drawing import DrawingVersion
from domain.exceptions import InvalidTransition
from domain.value_objects import RevisionCloud

# Draft -> Issued(IFC) -> Revised(clouded) -> Superseded
_ALLOWED: dict[str, set[str]] = {
    "DRAFT": {"ISSUED"},
    "ISSUED": {"REVISED", "SUPERSEDED"},
    "REVISED": {"SUPERSEDED"},
    "SUPERSEDED": set(),
}


def _check(version: DrawingVersion, to_status: str) -> None:
    if to_status not in _ALLOWED.get(version.status, set()):
        raise InvalidTransition("DrawingVersion", version.status, to_status)


def issue_version(version: DrawingVersion) -> DrawingVersion:
    _check(version, "ISSUED")
    return replace(version, status="ISSUED")


def mark_revised(version: DrawingVersion, clouds: list[RevisionCloud]) -> DrawingVersion:
    _check(version, "REVISED")
    return replace(version, status="REVISED", revision_clouds=list(clouds))


def supersede(version: DrawingVersion, superseded_by_id: int) -> DrawingVersion:
    _check(version, "SUPERSEDED")
    return replace(version, status="SUPERSEDED", superseded_by_id=superseded_by_id)
