"""Publishes to `keys.resolved` — the existing, frozen, unmodified
event-contracts schema (packages/event-contracts/keys_resolved.py).
Partition key is project_id, matching trigger.detected's own convention
(docs/03 §3), even though KeysResolved itself doesn't carry project_id as
a field — the partition key is transport-level, same pattern already
established for the connector -> ingestion handoff in Milestone 1."""

from __future__ import annotations

from event_contracts.topics import KEYS_RESOLVED
from event_contracts.keys_resolved import KeysResolved
from kafka import KafkaProducer

from config.settings import settings

_producer: KafkaProducer | None = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8"),
            value_serializer=lambda v: v.encode("utf-8"),
            acks="all",
            retries=5,
        )
    return _producer


def publish_keys_resolved(project_id: str, event: KeysResolved) -> None:
    producer = _get_producer()
    future = producer.send(KEYS_RESOLVED, key=project_id, value=event.model_dump_json())
    future.get(timeout=10)
