"""Milestone 0 — Kafka topic provisioning.

Provisions all ten frozen topics named in
docs/07_Downstream_Implementation_Blueprint.md §8 ("All ten are the
complete topic list this scope requires"), matching the same list already
encoded in packages/event-contracts/src/event_contracts/topics.py
(ALL_TOPICS). Milestone 1 only ever *publishes* to one of them
(trigger.detected) — the rest are provisioned now purely to satisfy
Milestone 0's own stated "done when" bar (blueprint §9: "the bus is up with
no consumers yet"), not because Milestone 1 uses them.

Idempotent: creating a topic that already exists is treated as success, not
an error (this script is safe to re-run against an already-provisioned bus).
"""

from __future__ import annotations

import os
import sys
import time

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

# Mirrors packages/event-contracts/src/event_contracts/topics.py ALL_TOPICS.
# Not imported directly to keep this bootstrap script dependency-free of the
# repo's own Python packages (it runs in its own minimal container, not
# inside any service's own image).
ALL_TOPICS = (
    "trigger.detected",
    "keys.resolved",
    "event.created",
    "impact.tiered",
    "severity.computed",
    "action.drafted",
    "action.approved",
    "action.dispatched",
    "action.confirmed",
    "event.closed",
)

# Small, fixed partition count — one demo project exists today; partitioned
# by project_id per docs/03 §3, sized for headroom, not current load.
PARTITIONS = 6
REPLICATION_FACTOR = 1  # single-broker dev topology (docs/07's own caveat: no HA in dev)


def wait_for_broker(bootstrap_servers: str, timeout_seconds: int = 60) -> KafkaAdminClient:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            return KafkaAdminClient(bootstrap_servers=bootstrap_servers, client_id="m0-bootstrap")
        except Exception as exc:  # noqa: BLE001 - broadly retry until the broker is reachable
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Kafka broker not reachable after {timeout_seconds}s: {last_error}")


def main() -> None:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "event-bus:9092")
    admin = wait_for_broker(bootstrap_servers)
    try:
        existing = set(admin.list_topics())
        to_create = [
            NewTopic(name=topic, num_partitions=PARTITIONS, replication_factor=REPLICATION_FACTOR)
            for topic in ALL_TOPICS
            if topic not in existing
        ]
        if not to_create:
            print("All ten topics already exist. Nothing to do.")
            return
        try:
            admin.create_topics(new_topics=to_create, validate_only=False)
        except TopicAlreadyExistsError:
            pass
        print(f"Provisioned {len(to_create)} topic(s): {[t.name for t in to_create]}")
        remaining = set(ALL_TOPICS) - set(admin.list_topics())
        if remaining:
            print(f"WARNING: topics still missing after create: {remaining}", file=sys.stderr)
            sys.exit(1)
        print(f"Verified: all {len(ALL_TOPICS)} topics present on {bootstrap_servers}.")
    finally:
        admin.close()


if __name__ == "__main__":
    main()
