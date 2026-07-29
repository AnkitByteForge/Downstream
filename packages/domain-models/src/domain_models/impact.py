"""Impact — the join between a Commercial Event and a Commercial Artifact.

Field set combines two sources, both frozen and both authoritative for a
different part of the shape:

- docs/03_Downstream_Systems_Architecture.md §7 names the full domain
  object, including `evidence_refs[]` and `action_id`.
- docs/07_Downstream_Implementation_Blueprint.md §6's `impacts` SQL table
  additionally carries a per-Impact `severity` (used throughout the
  Reference Execution Trace to rank impacts independently of their
  confidence tier) and gives the authoritative status enum: OPEN|CONTAINED.

Note: docs/05_Downstream_Reference_Execution_Trace.md's own illustrative SQL
(Phase 6) inserts impacts with status 'TRIAGED' — that value belongs to the
CommercialEvent status enum, not Impact's; the Implementation Blueprint's
schema comment (OPEN|CONTAINED) is treated here as authoritative for this
field, since docs/07 is the "translation only, nothing redesigned" handoff
specifically written to be implemented against.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain_models.commercial_event import MAX_SEVERITY, MIN_SEVERITY

ConfidenceTier = Literal["CERTAIN", "PROBABLE", "POSSIBLE"]
ImpactStatus = Literal["OPEN", "CONTAINED"]


class Impact(BaseModel):
    """The object that carries the interesting data for one affected
    Commercial Artifact: its confidence tier, the reason for that tier, its
    lifecycle position at detection time, its evidence, and its one Action.
    """

    model_config = ConfigDict(frozen=True)

    impact_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    artifact_ref: str = Field(min_length=1)

    confidence_tier: ConfidenceTier
    confidence_reason: str = Field(
        min_length=1,
        description="Always a plain-language reason, never a bare score (docs/03 §6c).",
    )
    lifecycle_position_at_detection: str | None = Field(
        default=None,
        description="The artifact's lifecycle position at the moment this Impact was computed; feeds severity.",
    )

    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to this Impact's Evidence citations (docs/03 §7).",
    )
    action_id: str | None = Field(
        default=None,
        description="The one Action drafted for this Impact, once drafted.",
    )

    severity: int = Field(ge=MIN_SEVERITY, le=MAX_SEVERITY)
    status: ImpactStatus = "OPEN"
