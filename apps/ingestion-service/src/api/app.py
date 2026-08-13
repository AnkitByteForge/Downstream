"""Ingestion & Normalization Service — Milestone 1's second half of the
chain. Receives an EngineeringEventEnvelope synchronously (blueprint §1's
direct, non-bus arrow from the connector), validates + dedups + filters, and
— for a genuinely new, event-worthy Trigger — persists it and publishes
`trigger.detected` (docs/03 Stage 2, Reference Execution Trace Phase 2)."""

from __future__ import annotations

import logging

from domain_models.trigger import Trigger
from event_contracts.trigger_detected import TriggerDetected
from fastapi import FastAPI, Response, status
from shared_config.ids import generate_id

from api.schemas import EnvelopeIn, IngestResultOut
from domain.event_worthiness import is_event_worthy
from publishers.kafka_publisher import publish_trigger_detected
from repository.idempotency_repository import build_dedup_key, existing_trigger_id, record
from repository.trigger_repository import insert

logger = logging.getLogger("ingestion-service")

app = FastAPI(title="Downstream — ingestion-service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/internal/envelopes", response_model=IngestResultOut)
def receive_envelope(body: EnvelopeIn, response: Response) -> IngestResultOut:
    envelope = body.envelope

    dedup_key = build_dedup_key(envelope.source_system, envelope.source_id, envelope.occurred_at)
    already = existing_trigger_id(dedup_key)
    if already is not None:
        logger.info("Envelope already ingested (dedup_key=%s) -> trigger_id=%s", dedup_key, already)
        response.status_code = status.HTTP_200_OK
        return IngestResultOut(trigger_id=already, outcome="deduped")

    if not is_event_worthy(envelope):
        logger.info(
            "Envelope not event-worthy (no spec/drawing/location refs), source_id=%s", envelope.source_id
        )
        response.status_code = status.HTTP_200_OK
        return IngestResultOut(trigger_id=None, outcome="filtered")

    trigger_id = generate_id("trigger")
    trigger = Trigger(
        trigger_id=trigger_id,
        project_id=body.project_id,
        type=envelope.type,
        # No envelope table exists anywhere in the frozen design (docs/03's
        # Connector Layer: "Storage at this boundary: none") — this is a
        # deterministic, reconstructable pointer, not a foreign key into a
        # persisted envelope row.
        source_envelope_ref=f"env_{envelope.source_system}_{envelope.source_id}_{envelope.occurred_at.isoformat()}",
        spec_section_refs=envelope.spec_section_refs,
        drawing_refs=envelope.drawing_refs,
        location_refs=envelope.location_refs,
        raw_document_ref=envelope.raw_document_ref,
        occurred_at=envelope.occurred_at,
    )
    insert(trigger)

    # Publish before recording the dedup entry, not after: if the Kafka
    # publish raises, the dedup row is never written, so a genuine RES
    # webhook redelivery for the same envelope can still be reprocessed
    # (docs/03: a failure must surface/retry, never silently vanish) rather
    # than being permanently deduped against a Trigger whose trigger.detected
    # message never actually landed on the bus. Found and fixed while
    # verifying this milestone against the real running stack, not assumed
    # correct from the reference trace's own happy-path-only illustration.
    publish_trigger_detected(
        TriggerDetected(trigger_id=trigger_id, project_id=body.project_id, occurred_at=envelope.occurred_at)
    )
    record(dedup_key, trigger_id)

    logger.info("Trigger persisted and trigger.detected published: %s", trigger_id)
    response.status_code = status.HTTP_201_CREATED
    return IngestResultOut(trigger_id=trigger_id, outcome="created")
