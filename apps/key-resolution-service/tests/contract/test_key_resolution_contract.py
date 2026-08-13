"""Contract test — runs against the REAL running stack: Postgres
(operational-db), Neo4j (with both engineering and commercial calibration
already run), and Kafka. Skipped unless KEY_RESOLUTION_CONTRACT_TESTS=1 is
set (see the Milestone 2 report for how to bring the stack up first).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.skipif(
    os.environ.get("KEY_RESOLUTION_CONTRACT_TESTS") != "1",
    reason="Set KEY_RESOLUTION_CONTRACT_TESTS=1 and point the KEY_RESOLUTION_* env vars at a live stack.",
)


def test_graph_repository_finds_the_real_23_31_13_match():
    from repository.graph_repository import find_purchase_orders_for_spec_section

    candidates = find_purchase_orders_for_spec_section("23 31 13")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.po_number == "4500018823"
    assert candidate.vendor_name == "VendorCo Metals"
    assert candidate.cost_code_native_code == "23-100"
    assert candidate.company_code == "1000"
    assert candidate.plant == "P100"


def test_graph_repository_returns_empty_for_a_spec_section_with_no_commercial_match():
    from repository.graph_repository import find_purchase_orders_for_spec_section

    candidates = find_purchase_orders_for_spec_section("23 74 13")  # SUB-118's RTU section — no matching CostCode
    assert candidates == []


def test_artifact_identity_upsert_is_idempotent():
    from domain.resolution import ResolvedCandidate
    from repository.artifact_identity_repository import upsert
    from repository.db import get_connection

    candidate = ResolvedCandidate(
        artifact_ref="po_1",
        match_basis="cost_code_exact",
        match_score=1.0,
        source_identifier="1",
        company_code="1000",
        plant="P100",
    )
    upsert("proj_meridian_tower", candidate)
    upsert("proj_meridian_tower", candidate)  # second call must not create a second row

    with get_connection() as conn:
        row = conn.execute(
            "SELECT count(*) FROM artifact_identity_map WHERE artifact_ref = %s AND source_system = %s",
            ("po_1", "reference-commercial-system"),
        ).fetchone()
    assert row[0] == 1


def test_full_pipeline_end_to_end_for_a_synthetic_trigger():
    """Exercises process_trigger_detected() directly (no Kafka framing) —
    inserts a throwaway Trigger row with the real spec_section_refs value,
    runs the real pipeline, and asserts the real resolution."""
    import uuid
    from datetime import datetime, timezone

    from consumers.trigger_detected_consumer import process_trigger_detected
    from repository.db import get_connection

    trigger_id = f"trg_contract_{uuid.uuid4().hex[:8]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO triggers (trigger_id, project_id, type, source_envelope_ref,
                                   spec_section_refs, drawing_refs, location_refs, occurred_at, status)
            VALUES (%s, 'proj_meridian_tower', 'RFI_APPROVED', 'env_contract_test',
                    '["23 31 13"]', '[]', '[]', %s, 'PENDING_RESOLUTION')
            """,
            (trigger_id, datetime.now(timezone.utc)),
        )

    event = process_trigger_detected(trigger_id)
    assert event.trigger_id == trigger_id
    assert len(event.candidates) == 1
    assert event.candidates[0].artifact_ref == "po_1"
    assert event.candidates[0].match_basis == "cost_code_exact"
    assert event.candidates[0].match_score == 1.0
