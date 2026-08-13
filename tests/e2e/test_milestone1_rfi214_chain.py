"""Milestone 1 acceptance test — the exact chain approved for this milestone:

    RES RFI-214 close -> webhook -> connector-procore -> RES GET-back
    -> EngineeringEventEnvelope -> ingestion-service -> Trigger persisted
    -> Kafka trigger.detected

Runs against the live, fully-up Docker Compose stack (infra/docker-compose.yml)
on its host-exposed ports. Skipped unless MILESTONE1_E2E=1 is set — this is
an acceptance test against real infrastructure, not something `pytest -q`
at the repo root should attempt against nothing running.

RECORDED LIMITATION, not silently resolved (see the Milestone 1 report):
RES's canonical seed (reference-systems/reference-engineering-system/backend/
src/seed/meridian_tower.py) closes RFI-214 via a direct domain
state-transition call (`rfi_transitions.close_rfi` + `repo.update`), not
through the `CloseRFI` *use case* that actually dispatches a webhook
(application/use_cases/rfi_use_cases.py). RFI-214 is therefore already
CLOSED (a terminal state — domain/state_machines/rfi_transitions.py's
_ALLOWED table has no outbound edge from CLOSED) by the time this test runs,
and RES exposes no REST endpoint to create a fresh RFI to close live. RES's
own test suite treats "RFI-214 CLOSED" as a locked invariant
(IMPLEMENTATION_STATUS.md RES-4G: "RFI-214 CLOSED sole Scenario-A trigger"),
so this milestone does not modify RES's seed to work around it — that risk
was judged worse than the alternative below.

This test instead constructs the exact thin webhook payload RES's own
dispatcher (infrastructure/webhooks/dispatcher.py + application/
webhook_payloads.py build_thin_payload) WOULD have produced had RFI-214's
close gone through the live use case, built entirely from RFI-214's real,
live data fetched from RES's real API — and delivers it to connector-procore's
real inbound endpoint. Every hop from there on is fully live: signature
verification, connector-procore's idempotency cache, the real RES enrichment
GET-back, the real reference-resolution calls, envelope construction, the
real synchronous handoff to ingestion-service, real Postgres persistence,
and a real Kafka publish — only the initial "RES's dispatcher calls out"
hop is reproduced rather than triggered live, because the seeded system
provides no live-closable RFI to trigger it from.
"""

from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
import psycopg
import pytest
from kafka import KafkaConsumer

pytestmark = pytest.mark.skipif(
    os.environ.get("MILESTONE1_E2E") != "1",
    reason="Set MILESTONE1_E2E=1 and bring up infra/docker-compose.yml first (see the Milestone 1 report).",
)

RES_BASE_URL = os.environ.get("RES_BASE_URL", "http://localhost:8000")
CONNECTOR_BASE_URL = os.environ.get("CONNECTOR_PROCORE_BASE_URL", "http://localhost:8080")
OPERATIONAL_DB_URL = os.environ.get(
    "OPERATIONAL_DB_URL", "postgresql://postgres@localhost:5432/downstream_operational"
)
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")  # EXTERNAL listener
DOWNSTREAM_PROJECT_ID = "proj_meridian_tower"
WEBHOOK_SECRET = "seed-webhook-secret"  # matches meridian_tower.py DEFAULT_WEBHOOK_SECRET


_timestamp_nonce = itertools.count()


def _unique_timestamp() -> str:
    """A strictly-increasing, collision-free timestamp per call within this
    test process. Plain `datetime.now(timezone.utc).isoformat()` collided
    across two test functions run moments apart in this environment
    (observed live: Windows' effective clock resolution was coarse enough
    for two separate calls to produce the identical string, which the
    idempotency cache then — correctly — treated as one real event). Each
    test genuinely wants a *fresh, distinct* logical event, so this adds a
    monotonic microsecond offset rather than trusting wall-clock resolution."""
    return (datetime.now(timezone.utc) + timedelta(microseconds=next(_timestamp_nonce))).isoformat()


def _res_token() -> str:
    resp = httpx.post(
        f"{RES_BASE_URL}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "downstream-partial",
            "client_secret": "partial-scope-secret",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _fetch_rfi_214() -> tuple[int, dict]:
    token = _res_token()
    headers = {"Authorization": f"Bearer {token}"}
    projects = httpx.get(f"{RES_BASE_URL}/rest/v1.0/projects", headers=headers, timeout=10.0).json()
    project_id = projects[0]["id"]
    rfis = httpx.get(
        f"{RES_BASE_URL}/rest/v1.0/projects/{project_id}/rfis",
        headers=headers,
        params={"per_page": 100},
        timeout=10.0,
    ).json()
    rfi = next(r for r in rfis if r["display_number"] == "RFI-214")
    assert rfi["status"] == "CLOSED", "RFI-214 must already be closed in RES's canonical seed"
    return project_id, rfi


def _build_signed_webhook(res_project_id: int, rfi_id: int, timestamp: str) -> tuple[bytes, str]:
    payload = {
        "resource_name": "rfis",
        "resource_id": rfi_id,
        "project_id": res_project_id,
        "event_type": "update",
        "timestamp": timestamp,
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, signature


def _send_webhook(body: bytes, signature: str) -> httpx.Response:
    return httpx.post(
        f"{CONNECTOR_BASE_URL}/connectors/procore/{DOWNSTREAM_PROJECT_ID}",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": signature},
        timeout=15.0,
    )


def _query_trigger(trigger_id: str) -> dict | None:
    with psycopg.connect(OPERATIONAL_DB_URL) as conn:
        row = conn.execute(
            """
            SELECT trigger_id, project_id, type, spec_section_refs, drawing_refs,
                   location_refs, status, occurred_at
            FROM triggers WHERE trigger_id = %s
            """,
            (trigger_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "trigger_id": row[0],
        "project_id": row[1],
        "type": row[2],
        "spec_section_refs": row[3],
        "drawing_refs": row[4],
        "location_refs": row[5],
        "status": row[6],
        "occurred_at": row[7],
    }


def _count_triggers_for_project(project_id: str) -> int:
    with psycopg.connect(OPERATIONAL_DB_URL) as conn:
        row = conn.execute("SELECT count(*) FROM triggers WHERE project_id = %s", (project_id,)).fetchone()
        return row[0]


def _consume_trigger_detected(expected_trigger_id: str, timeout_seconds: int = 20) -> dict | None:
    """Manual partition assignment, not a `group_id` subscription: this is a
    one-shot 'did the message land' check with no offset-commit or
    rebalancing need, and consumer-group coordinator negotiation
    (JoinGroup/SyncGroup) proved unreliable against kafka-python-ng's
    Windows socket-selector handling when actually run against the live
    stack — found while verifying this milestone, not assumed working from
    the library's README. Manual assignment skips the group coordinator
    entirely, which is both simpler and the more robust choice here."""
    from kafka import TopicPartition

    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        consumer_timeout_ms=5000,
    )
    try:
        partitions = consumer.partitions_for_topic("trigger.detected") or set()
        topic_partitions = [TopicPartition("trigger.detected", p) for p in partitions]
        consumer.assign(topic_partitions)
        consumer.seek_to_beginning(*topic_partitions)

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            batches = consumer.poll(timeout_ms=2000)
            for records in batches.values():
                for record in records:
                    if record.value.get("trigger_id") == expected_trigger_id:
                        return record.value
    finally:
        consumer.close()
    return None


def test_full_milestone1_chain_rfi214_close_to_kafka():
    """NOTE on repeatability against a persistent environment: RFI-214's
    envelope.occurred_at is RES's own real, fixed closed_at timestamp — it
    never changes no matter how many times this test constructs a "new"
    outer webhook wrapper (a genuinely different outer `timestamp` field
    passes connector-procore's own idempotency cache every time, correctly,
    but ingestion-service's *separate* dedup layer, keyed on
    (source_system, source_id, occurred_at), correctly recognizes every one
    of them as the same underlying real event once any one of them has ever
    been ingested in this environment's lifetime). So only the first run
    against a given fresh environment observes outcome="created" — every
    later run correctly observes "deduped", which is the system doing
    exactly what docs/03's idempotency design calls for, not a test flake.
    This test accepts either outcome and still verifies the full chain via
    whichever trigger_id comes back.
    """
    res_project_id, rfi = _fetch_rfi_214()
    timestamp = _unique_timestamp()
    body, signature = _build_signed_webhook(res_project_id, rfi["id"], timestamp)

    resp = _send_webhook(body, signature)
    assert resp.status_code == 202
    result = resp.json()
    assert result["outcome"] in ("created", "deduped")
    trigger_id = result["trigger_id"]
    assert trigger_id is not None

    trigger = _query_trigger(trigger_id)
    assert trigger is not None
    assert trigger["project_id"] == DOWNSTREAM_PROJECT_ID
    assert trigger["type"] == "RFI_APPROVED"
    # Milestone 2 (approved remedy (a)): connector-procore now uses RES's
    # full-scope credential (infra/scripts/seed_connector_configuration.sql),
    # not Milestone 1's partial-scope one — verified live in M1 to silently
    # drop spec_sections/locations. All three reference lists now resolve.
    # This assumes a genuinely fresh environment (a "deduped" outcome against
    # a stale pre-Milestone-2 environment would return an old Trigger row
    # still carrying the empty lists) — the documented verification
    # procedure always brings the stack up from `docker compose down -v`.
    assert trigger["spec_section_refs"] == ["23 31 13"]
    assert {"item_id": "M-2.1", "version_id": "Rev C"} in trigger["drawing_refs"]
    assert trigger["location_refs"] == ["Grid B-4"]
    assert trigger["status"] == "PENDING_RESOLUTION"

    kafka_message = _consume_trigger_detected(trigger_id)
    assert kafka_message is not None, "no trigger.detected message observed for this trigger_id"
    assert kafka_message["project_id"] == DOWNSTREAM_PROJECT_ID
    assert kafka_message["trigger_id"] == trigger_id


def test_redelivery_of_the_same_webhook_is_idempotent():
    """Reference Execution Trace Phase 1.1 / docs/03: connector-level
    idempotency is 'the system's first and most important defense' against
    at-least-once webhook redelivery."""
    res_project_id, rfi = _fetch_rfi_214()
    timestamp = _unique_timestamp()
    body, signature = _build_signed_webhook(res_project_id, rfi["id"], timestamp)

    first = _send_webhook(body, signature)
    assert first.status_code == 202
    first_result = first.json()
    # Either is a legitimate outcome against a persistent, already-exercised
    # environment — see test_full_milestone1_chain_rfi214_close_to_kafka's
    # docstring. What this test actually verifies is the *second*, truly
    # identical send below.
    assert first_result["outcome"] in ("created", "deduped")
    trigger_id = first_result["trigger_id"]

    before_redelivery_count = _count_triggers_for_project(DOWNSTREAM_PROJECT_ID)

    second = _send_webhook(body, signature)  # exact same body + signature = a real redelivery
    assert second.status_code == 202
    second_result = second.json()
    assert second_result["outcome"] == "duplicate_ignored"

    after_redelivery_count = _count_triggers_for_project(DOWNSTREAM_PROJECT_ID)
    assert after_redelivery_count == before_redelivery_count, "redelivery must not create a second Trigger"

    # The first delivery's own Trigger is still there, untouched.
    trigger = _query_trigger(trigger_id)
    assert trigger is not None
