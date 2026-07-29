"""Schema for the `event.closed` topic.

Emitted by: Commercial Event Service. Consumed by: Ledger, Realtime Gateway.
Exact shape per Phase 15 of docs/05_Downstream_Reference_Execution_Trace.md
(`Emitted: event.closed { event_id: evt_7731 }`), matching
docs/07_Downstream_Implementation_Blueprint.md §7's WebSocket contract
(`{ topic: "event.closed", event_id }`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EventClosed(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
