"""Contract test for POST /internal/envelopes against a REAL Postgres
(triggers, ingestion_idempotency tables) and REAL Kafka (trigger.detected
topic) — the full Ingestion & Normalization Service behavior docs/03 Stage 2
and docs/05 Phase 2 describe. Skipped automatically unless
INGESTION_CONTRACT_TESTS=1 is set (run against the live Docker Compose
stack; see the Milestone 1 report for how to bring it up).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.skipif(
    os.environ.get("INGESTION_CONTRACT_TESTS") != "1",
    reason="Set INGESTION_CONTRACT_TESTS=1 and point INGESTION_DATABASE_URL / "
    "INGESTION_KAFKA_BOOTSTRAP_SERVERS at a live stack to run this test.",
)


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from api.app import app

    return TestClient(app)


def _envelope_payload(source_id: str, occurred_at: str) -> dict:
    return {
        "project_id": "proj_meridian_tower",
        "envelope": {
            "envelope_type": "EngineeringEventEnvelope",
            "source_system": "procore",
            "source_id": source_id,
            "display_number": "RFI-214",
            "type": "RFI_APPROVED",
            "spec_section_refs": ["23 31 13"],
            "drawing_refs": [{"item_id": "M-2.1", "version_id": "Rev C"}],
            "location_refs": ["Grid B-4"],
            "raw_document_ref": "engineering://attachments/SK-14_reroute.pdf",
            "region": None,
            "acting_credential_scope": "partial:[documents,rfis,submittals]",
            "occurred_at": occurred_at,
        },
    }


def test_new_envelope_creates_trigger_and_publishes(client):
    occurred_at = datetime.now(timezone.utc).isoformat()
    resp = client.post("/internal/envelopes", json=_envelope_payload("contract-test-1", occurred_at))
    assert resp.status_code == 201
    body = resp.json()
    assert body["outcome"] == "created"
    assert body["trigger_id"] is not None


def test_resubmitting_the_same_envelope_is_deduped(client):
    occurred_at = datetime.now(timezone.utc).isoformat()
    payload = _envelope_payload("contract-test-2", occurred_at)
    first = client.post("/internal/envelopes", json=payload)
    second = client.post("/internal/envelopes", json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["outcome"] == "deduped"
    assert second.json()["trigger_id"] == first.json()["trigger_id"]


def test_envelope_with_no_references_is_filtered_not_persisted(client):
    occurred_at = datetime.now(timezone.utc).isoformat()
    payload = _envelope_payload("contract-test-3", occurred_at)
    payload["envelope"]["spec_section_refs"] = []
    payload["envelope"]["drawing_refs"] = []
    payload["envelope"]["location_refs"] = []
    resp = client.post("/internal/envelopes", json=payload)
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "filtered"
    assert resp.json()["trigger_id"] is None
