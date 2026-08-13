"""Synchronous handoff to ingestion-service — the direct (non-event-bus)
arrow in blueprint §1's architecture diagram ("PADAPT -->|EngineeringEventEnvelope|
INGEST"). docs/03 §3's canonical topics table starts at trigger.detected,
confirming Connector -> Ingestion is not an event-bus hop.

EngineeringEventEnvelope itself carries no project_id field (docs/03 §1's
literal envelope shape has none — project scoping is transport-level context,
carried the same way blueprint §7's inbound webhook contract carries it in
the URL path: `POST /connectors/procore/{project_id}`). This client therefore
sends project_id as a sibling field alongside the envelope, not inside it —
ingestion-service's own request schema (api/schemas.py EnvelopeIn) mirrors
this shape.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from envelope_schemas import EngineeringEventEnvelope


@dataclass
class IngestResult:
    status_code: int
    trigger_id: str | None
    outcome: str  # "created" | "deduped" | "filtered"


def submit_envelope(
    ingestion_service_url: str, project_id: str, envelope: EngineeringEventEnvelope, timeout_seconds: float = 10.0
) -> IngestResult:
    resp = httpx.post(
        f"{ingestion_service_url}/internal/envelopes",
        json={"project_id": project_id, "envelope": envelope.model_dump(mode="json")},
        timeout=timeout_seconds,
    )
    resp.raise_for_status()
    body = resp.json()
    return IngestResult(status_code=resp.status_code, trigger_id=body.get("trigger_id"), outcome=body["outcome"])
