"""Schema for the `event.created` topic.

Emitted by: Commercial Event Service (per
docs/07_Downstream_Implementation_Blueprint.md §5's communication map — note
docs/03_Downstream_Systems_Architecture.md §3's topic table lists the
Reasoning Pipeline as emitter; the Reasoning Pipeline *produces* the
Event/Impact/Action data that the Commercial Event Service then writes and
emits from, so docs/07 §5 is followed here as the more implementation-
specific of the two).

Shape includes `project_id` because the Realtime Gateway forwards this
message to the frontend *verbatim* (docs/03 §12: "everything it forwards
already exists as a real domain event"), and docs/07 §7's WebSocket
contract for this exact topic explicitly includes project_id — the bus
payload must already carry it for that forwarding guarantee to hold.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain_models.commercial_event import MAX_SEVERITY, MIN_SEVERITY


class EventCreated(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    severity: int = Field(ge=MIN_SEVERITY, le=MAX_SEVERITY)
