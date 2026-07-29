"""Trigger — the first durable internal object in the system.

Shape per docs/03_Downstream_Systems_Architecture.md §2 ("Trigger (internal
object)"), with `created_at` added per the persisted `triggers` table in
docs/07_Downstream_Implementation_Blueprint.md §6.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from envelope_schemas.engineering_event_envelope import DrawingRef, EngineeringEventType

# Only "PENDING_RESOLUTION" is ever named, in any of the frozen documents, as
# a concrete Trigger status value (docs/03 §2 and the Consistency/idempotency
# section). No other status value is spelled out anywhere, so — rather than
# invent transition states nothing in the frozen design names — this is kept
# as a plain string with that documented default, not a closed Literal enum.
TRIGGER_STATUS_PENDING_RESOLUTION = "PENDING_RESOLUTION"


class Trigger(BaseModel):
    """A normalized, project-scoped candidate for a Commercial Event.

    Persisted by the Ingestion & Normalization Service — the first durable
    write in the whole pipeline (docs/03 §2).
    """

    model_config = ConfigDict(frozen=True)

    trigger_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    type: EngineeringEventType
    source_envelope_ref: str = Field(
        min_length=1,
        description="A pointer to the EngineeringEventEnvelope this Trigger was normalized from.",
    )

    spec_section_refs: list[str] = Field(default_factory=list)
    drawing_refs: list[DrawingRef] = Field(default_factory=list)
    location_refs: list[str] = Field(default_factory=list)
    raw_document_ref: str | None = None

    occurred_at: datetime
    status: str = Field(
        default=TRIGGER_STATUS_PENDING_RESOLUTION,
        min_length=1,
        description="Only 'PENDING_RESOLUTION' is named in the frozen docs; see module docstring.",
    )
    created_at: datetime | None = Field(
        default=None,
        description="When this Trigger was persisted; set by the owning service, not the caller.",
    )
