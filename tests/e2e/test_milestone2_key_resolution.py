"""Milestone 2 acceptance test — the exact chain approved for this
milestone, extending Milestone 1's own acceptance test:

    RES RFI-214 close -> webhook -> connector-procore -> RES GET-back
    -> EngineeringEventEnvelope -> ingestion-service -> Trigger persisted
    -> Kafka trigger.detected -> key-resolution-service
    -> SpecSection "23 31 13" resolved against the real graph
    -> CostCode "23-100" -> POLine -> PurchaseOrder 4500018823 -> VendorCo Metals
    -> keys.resolved published -> artifact_identity_map row written

Runs against the live, fully-up Docker Compose stack on its host-exposed
ports. Skipped unless MILESTONE2_E2E=1 is set. Requires: RES seeded, RCS
seeded, engineering graph calibration (seed_graph.py) and commercial graph
calibration (seed_graph_commercial.py) both run, connector-procore using
the full-scope RES credential (Milestone 2 remedy (a)), and
key-resolution-service running.

Same recorded limitation as Milestone 1's own e2e test (see that file's
module docstring): RES's canonical seed closes RFI-214 via a direct domain
transition, not the CloseRFI use case that dispatches a webhook, so this
test constructs the real thin webhook payload RES's dispatcher would have
produced from RFI-214's real, live data rather than triggering the close
live.
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
from kafka import KafkaConsumer, TopicPartition

pytestmark = pytest.mark.skipif(
    os.environ.get("MILESTONE2_E2E") != "1",
    reason="Set MILESTONE2_E2E=1 and bring up infra/docker-compose.yml first (see the Milestone 2 report).",
)

RES_BASE_URL = os.environ.get("RES_BASE_URL", "http://localhost:8000")
CONNECTOR_BASE_URL = os.environ.get("CONNECTOR_PROCORE_BASE_URL", "http://localhost:8080")
OPERATIONAL_DB_URL = os.environ.get(
    "OPERATIONAL_DB_URL", "postgresql://postgres@localhost:5432/downstream_operational"
)
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
DOWNSTREAM_PROJECT_ID = "proj_meridian_tower"
WEBHOOK_SECRET = "seed-webhook-secret"
EXPECTED_ARTIFACT_REF = "po_1"

_timestamp_nonce = itertools.count()


def _unique_timestamp() -> str:
    return (datetime.now(timezone.utc) + timedelta(microseconds=next(_timestamp_nonce))).isoformat()


def _res_token() -> str:
    resp = httpx.post(
        f"{RES_BASE_URL}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "downstream-full",
            "client_secret": "full-scope-secret",
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
    assert rfi["status"] == "CLOSED"
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


def _fire_rfi_214_and_get_trigger_id() -> str:
    res_project_id, rfi = _fetch_rfi_214()
    timestamp = _unique_timestamp()
    body, signature = _build_signed_webhook(res_project_id, rfi["id"], timestamp)
    resp = _send_webhook(body, signature)
    assert resp.status_code == 202
    result = resp.json()
    assert result["outcome"] in ("created", "deduped")
    trigger_id = result["trigger_id"]
    assert trigger_id is not None
    return trigger_id


def _consume_topic_for_trigger(topic: str, trigger_id: str, timeout_seconds: int = 30) -> dict | None:
    """Manual partition assignment — same reliability fix as Milestone 1's
    e2e test and key-resolution-service's own consumer (this stack's
    single-broker KRaft Kafka never completes consumer-group coordinator
    negotiation)."""
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=5000,
    )
    try:
        partitions = consumer.partitions_for_topic(topic) or set()
        topic_partitions = [TopicPartition(topic, p) for p in partitions]
        consumer.assign(topic_partitions)
        consumer.seek_to_beginning(*topic_partitions)

        deadline = time.monotonic() + timeout_seconds
        latest_match: dict | None = None
        while time.monotonic() < deadline:
            batches = consumer.poll(timeout_ms=2000)
            for records in batches.values():
                for record in records:
                    if record.value.get("trigger_id") == trigger_id:
                        latest_match = record.value
            if latest_match is not None:
                return latest_match
    finally:
        consumer.close()
    return latest_match


def _query_artifact_identity_map(artifact_ref: str) -> dict | None:
    with psycopg.connect(OPERATIONAL_DB_URL) as conn:
        row = conn.execute(
            """
            SELECT artifact_ref, project_id, source_system, source_identifier, org_scope
            FROM artifact_identity_map WHERE artifact_ref = %s AND source_system = %s
            """,
            (artifact_ref, "reference-commercial-system"),
        ).fetchone()
    if row is None:
        return None
    return {
        "artifact_ref": row[0],
        "project_id": row[1],
        "source_system": row[2],
        "source_identifier": row[3],
        "org_scope": row[4],
    }


def _count_artifact_identity_rows(artifact_ref: str) -> int:
    with psycopg.connect(OPERATIONAL_DB_URL) as conn:
        row = conn.execute(
            "SELECT count(*) FROM artifact_identity_map WHERE artifact_ref = %s AND source_system = %s",
            (artifact_ref, "reference-commercial-system"),
        ).fetchone()
        return row[0]


def test_full_milestone2_chain_rfi214_to_vendorco_metals():
    trigger_id = _fire_rfi_214_and_get_trigger_id()

    keys_resolved = _consume_topic_for_trigger("keys.resolved", trigger_id)
    assert keys_resolved is not None, "no keys.resolved message observed for this trigger_id"
    assert len(keys_resolved["candidates"]) == 1
    candidate = keys_resolved["candidates"][0]
    assert candidate["artifact_ref"] == EXPECTED_ARTIFACT_REF
    assert candidate["match_basis"] == "cost_code_exact"
    assert candidate["match_score"] == 1.0

    row = _query_artifact_identity_map(EXPECTED_ARTIFACT_REF)
    assert row is not None
    assert row["project_id"] == DOWNSTREAM_PROJECT_ID
    assert row["source_identifier"] == "1"
    assert row["org_scope"]["company_code"] == "1000"
    assert row["org_scope"]["plant"] == "P100"


def test_full_real_graph_path_in_neo4j():
    from neo4j import GraphDatabase

    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "downstream-dev"))
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (r:RFI)-[:REFERENCES]->(s:SpecSection {number: '23 31 13'})
                      -[:PROCURED_UNDER]->(c:CostCode {native_code: '23-100'})
                      -[:LINE_ITEM_OF]->(l:POLine)<-[:HAS_LINE]-(p:PurchaseOrder {po_number: '4500018823'})
                      -[:SUPPLIED_BY]->(v:Vendor {name: 'VendorCo Metals'})
                RETURN r.display_number AS rfi, l.lifecycle_position AS lifecycle_position, l.value AS value
                """
            ).single()
    finally:
        driver.close()
    assert result is not None, "the full real path RFI-214 -> ... -> VendorCo Metals is not in the graph"
    assert result["rfi"] == "RFI-214"
    assert result["lifecycle_position"] == "in_fabrication"
    assert result["value"] == 820000.0


def test_redelivery_does_not_duplicate_artifact_identity_map_row():
    before = _count_artifact_identity_rows(EXPECTED_ARTIFACT_REF)
    assert before >= 1  # the first test in this module already created it

    trigger_id = _fire_rfi_214_and_get_trigger_id()  # a genuine redelivery/reprocessing of the same real event
    _consume_topic_for_trigger("keys.resolved", trigger_id)  # let key-resolution-service catch up

    after = _count_artifact_identity_rows(EXPECTED_ARTIFACT_REF)
    assert after == before, "redelivery must not create a second artifact_identity_map row for the same artifact"
