"""Schema for the `keys.resolved` topic.

Emitted by: Key Resolution Service. Consumed by: Graph Layer (write),
Reasoning Pipeline (read). Exact shape per Phase 3 of
docs/05_Downstream_Reference_Execution_Trace.md, whose candidate objects
match the `(trigger_id, artifact_ref, match_score, match_basis)` tuple
named in docs/03_Downstream_Systems_Architecture.md §4.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KeyCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_ref: str = Field(min_length=1)
    match_basis: str = Field(
        min_length=1,
        description="e.g. 'cost_code_exact', 'graph_edge:structural_dependency'.",
    )
    match_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Match-quality score — raw material for Confidence Tiering, not itself a confidence tier.",
    )


class KeysResolved(BaseModel):
    model_config = ConfigDict(frozen=True)

    trigger_id: str = Field(min_length=1)
    candidates: list[KeyCandidate] = Field(default_factory=list)
