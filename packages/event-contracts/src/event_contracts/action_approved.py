"""Schema for the `action.approved` topic.

Emitted by: Approval Service. Consumed by: Synchronization Service, Ledger.
Exact shape per Phase 11.2 of
docs/05_Downstream_Reference_Execution_Trace.md
(`Emitted: action.approved { action_id: act_001 }`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActionApproved(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
