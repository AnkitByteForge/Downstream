"""Schema for the `action.confirmed` topic.

Emitted by: Synchronization Service (receipt handler). Consumed by:
Commercial Event Service, Ledger, Realtime Gateway. Exact shape per Phase
11.4 of docs/05_Downstream_Reference_Execution_Trace.md
(`emits action.confirmed { action_id: act_001 }`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActionConfirmed(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
