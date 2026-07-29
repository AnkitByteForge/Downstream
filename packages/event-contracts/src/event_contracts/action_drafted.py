"""Schema for the `action.drafted` topic.

Emitted by: Reasoning Pipeline (Grounded Drafting sub-stage). Consumed by:
Commercial Event Service, Ledger. Exact shape per Phase 6 of
docs/05_Downstream_Reference_Execution_Trace.md
(`action.drafted { action_id: act_001 }`, one message per drafted Action).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActionDrafted(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
