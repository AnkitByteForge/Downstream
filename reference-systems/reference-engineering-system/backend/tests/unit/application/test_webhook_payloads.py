from __future__ import annotations

from datetime import datetime, timezone

from application.webhook_payloads import build_thin_payload

TRACE_TIMESTAMP = datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)


def test_thin_payload_has_exactly_five_fields():
    payload = build_thin_payload("rfis", 4821356, 8841, "update", TRACE_TIMESTAMP)
    assert set(payload.keys()) == {
        "resource_name",
        "resource_id",
        "project_id",
        "event_type",
        "timestamp",
    }


def test_thin_payload_matches_reference_trace_phase_0_shape():
    payload = build_thin_payload("rfis", 4821356, 884199, "update", TRACE_TIMESTAMP)
    assert payload == {
        "resource_name": "rfis",
        "resource_id": 4821356,
        "project_id": 884199,
        "event_type": "update",
        "timestamp": "2026-07-28T09:14:03+00:00",
    }
