from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RevisionCloud:
    """One clouded, delta-numbered change area on a drawing revision
    (Reference Engineering System doc §4/§7). Only the current version's
    clouds are ever shown; prior clouds are retained in history, not deleted.
    """

    area: str
    delta_number: int
    description: str
