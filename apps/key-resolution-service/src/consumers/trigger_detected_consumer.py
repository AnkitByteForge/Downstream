"""Consumes `trigger.detected`, resolves the Trigger's real spec_section_refs
against the graph's real SpecSection<->CostCode business-key match, writes
artifact_identity_map, and publishes `keys.resolved` — docs/03 §4's Key
Resolution stage, Milestone 2 scope only (no Reasoning, no severity, no
confidence tier)."""

from __future__ import annotations

import json
import logging

from event_contracts.keys_resolved import KeyCandidate, KeysResolved
from kafka import KafkaConsumer, TopicPartition

from config.settings import settings
from domain.resolution import resolve_candidates
from publishers.keys_resolved_publisher import publish_keys_resolved
from repository.artifact_identity_repository import upsert as upsert_artifact_identity
from repository.graph_repository import find_purchase_orders_for_spec_section
from repository.trigger_repository import get_trigger

logger = logging.getLogger("key-resolution-service")


def process_trigger_detected(trigger_id: str) -> KeysResolved:
    """The whole resolution pipeline for one Trigger, factored out of the
    Kafka loop so it's directly testable (contract tests call this with a
    real trigger_id against real Postgres/Neo4j/Kafka, no message framing
    involved)."""
    trigger = get_trigger(trigger_id)
    if trigger is None:
        logger.warning("trigger.detected referenced unknown trigger_id=%s — nothing to resolve.", trigger_id)
        event = KeysResolved(trigger_id=trigger_id, candidates=[])
        publish_keys_resolved("unknown", event)
        return event

    # Milestone 2 scope: only spec_section_refs has a defined
    # engineering-to-commercial join today (SpecSection -> CostCode).
    # drawing_refs/location_refs are read (per the frozen Trigger contract)
    # but produce no commercial candidates — no join path involves them yet,
    # which is a real, honest boundary, not a gap this service routes around.
    all_candidates = []
    for spec_section_ref in trigger.spec_section_refs:
        commercial_matches = find_purchase_orders_for_spec_section(spec_section_ref)
        all_candidates.extend(resolve_candidates(commercial_matches))

    for candidate in all_candidates:
        upsert_artifact_identity(trigger.project_id, candidate)

    event = KeysResolved(
        trigger_id=trigger_id,
        candidates=[
            KeyCandidate(artifact_ref=c.artifact_ref, match_basis=c.match_basis, match_score=c.match_score)
            for c in all_candidates
        ],
    )
    publish_keys_resolved(trigger.project_id, event)

    if all_candidates:
        logger.info(
            "trigger_id=%s resolved %d candidate(s): %s",
            trigger_id,
            len(all_candidates),
            [c.artifact_ref for c in all_candidates],
        )
    else:
        logger.info(
            "trigger_id=%s resolved 0 candidates (spec_section_refs=%s) — published empty keys.resolved, "
            "not silently skipped.",
            trigger_id,
            trigger.spec_section_refs,
        )
    return event


def run_forever() -> None:
    """Manual partition assignment, not a `group_id` subscription — found
    live, against this stack's real single-broker KRaft Kafka, that
    consumer-group coordinator negotiation (JoinGroup/SyncGroup) never
    succeeds (repeated NotCoordinatorForGroupError, the same class of
    kafka-python-ng/Windows-socket flakiness already found and worked
    around in the Milestone 1 e2e test's own Kafka consumer). Manual
    assignment skips the group coordinator entirely.

    Re-seeks to the beginning of every partition on every process start,
    reprocessing already-seen trigger.detected messages — safe and cheap
    because every write this service performs (Neo4j reads, graph-derived
    artifact_identity_map upsert, keys.resolved publish) is idempotent by
    construction (this milestone's own explicit idempotency requirement),
    not because messages are assumed few. No committed-offset tracking is
    introduced — consistent with the approved instruction not to add a new
    relational dedup table unless the architecture actually requires one.
    """
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    partitions = consumer.partitions_for_topic("trigger.detected") or set()
    topic_partitions = [TopicPartition("trigger.detected", p) for p in partitions]
    consumer.assign(topic_partitions)
    consumer.seek_to_beginning(*topic_partitions)

    logger.info("key-resolution-service consuming trigger.detected (manual partition assignment)")
    while True:
        batches = consumer.poll(timeout_ms=2000)
        for records in batches.values():
            for record in records:
                trigger_id = record.value["trigger_id"]
                try:
                    process_trigger_detected(trigger_id)
                except Exception:
                    # poll() advances past this record regardless; a failure
                    # here is only retried on the next process restart
                    # (which re-seeks to the beginning), not on the next
                    # poll() call within this same run.
                    logger.exception(
                        "Failed to process trigger_id=%s — will be retried on next service restart.", trigger_id
                    )
