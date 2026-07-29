"""Schema for the `impact.tiered` topic.

Emitted by: Reasoning Pipeline (Confidence Tiering sub-stage). Consumed by:
Commercial Event Service, Ledger, Realtime Gateway. Shape combines Phase 6
of docs/05_Downstream_Reference_Execution_Trace.md (`impact_id, tier,
severity`) with the identical field list in the Realtime Gateway's
WebSocket contract, docs/07_Downstream_Implementation_Blueprint.md §7
(`{ topic: "impact.tiered", impact_id, tier, severity }`) — both sources
agree, and neither includes `project_id` for this topic.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain_models.commercial_event import MAX_SEVERITY, MIN_SEVERITY
from domain_models.impact import ConfidenceTier


class ImpactTiered(BaseModel):
    model_config = ConfigDict(frozen=True)

    impact_id: str = Field(min_length=1)
    tier: ConfidenceTier
    severity: int = Field(ge=MIN_SEVERITY, le=MAX_SEVERITY)
