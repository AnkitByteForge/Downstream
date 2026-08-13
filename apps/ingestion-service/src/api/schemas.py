"""Request/response shapes for the synchronous connector -> ingestion
handoff. EngineeringEventEnvelope itself carries no project_id field
(docs/03 §1's literal shape has none) so project_id travels as a sibling
field, mirroring blueprint §7's URL-path-scoped inbound webhook contract —
see client/ingestion_client.py in connector-procore for the matching
producer side of this contract."""

from __future__ import annotations

from envelope_schemas import EngineeringEventEnvelope
from pydantic import BaseModel


class EnvelopeIn(BaseModel):
    project_id: str
    envelope: EngineeringEventEnvelope


class IngestResultOut(BaseModel):
    trigger_id: str | None
    outcome: str  # "created" | "deduped" | "filtered"
