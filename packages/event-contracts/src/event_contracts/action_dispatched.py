"""Schema for the `action.dispatched` topic.

Emitted by: Synchronization Service. Consumed by: Ledger, Realtime Gateway.
Exact shape per Phase 11.3 of docs/05_Downstream_Reference_Execution_Trace.md
(`Emitted: action.dispatched { action_id: act_001 }`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActionDispatched(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
