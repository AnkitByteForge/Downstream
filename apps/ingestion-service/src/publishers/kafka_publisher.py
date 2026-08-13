"""Publishes to `trigger.detected` — docs/03 Stage 2's emission, the only
topic this milestone's own pipeline actually produces onto. Partition key is
project_id, per docs/03 §3 / packages/event-contracts topics.py
PARTITION_KEY_FIELD."""

from __future__ import annotations

from kafka import KafkaProducer

from event_contracts.topics import TRIGGER_DETECTED
from event_contracts.trigger_detected import TriggerDetected

from config.settings import settings

_producer: KafkaProducer | None = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8"),
            value_serializer=lambda v: v.encode("utf-8"),
            # At-least-once (docs/03 §3's actual delivery guarantee — not
            # exactly-once, so no idempotent-producer config is required):
            # acks='all' waits for the (single, dev-topology) broker to
            # confirm the write before returning; retries covers transient
            # send failures. kafka-python-ng has no enable_idempotence
            # option (that's a librdkafka/confluent-kafka concept) — found
            # and removed while bringing this stack up for real, not
            # assumed compatible from the client library's name alone.
            acks="all",
            retries=5,
        )
    return _producer


def publish_trigger_detected(event: TriggerDetected) -> None:
    producer = _get_producer()
    future = producer.send(
        TRIGGER_DETECTED,
        key=event.project_id,
        value=event.model_dump_json(),
    )
    future.get(timeout=10)  # block for the send to be acknowledged, so a caller knows it landed
