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
    source_evidence_ref: str | None = None
    """Opaque pointer into an external evidence system (ADR-009) — e.g. a
    Document Ingestion Pipeline reference. RES never parses, validates the
    shape of, or derives meaning from this value; it is a citation RES
    stores on the engineering-domain's behalf, not a fact RES owns.
    Nullable and defaulted for backward compatibility with every
    RevisionCloud constructed before ADR-009 (Meridian Tower's existing
    seed data)."""
