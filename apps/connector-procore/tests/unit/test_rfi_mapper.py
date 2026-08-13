"""Pure-logic unit test for raw-RES-payload -> EngineeringEventEnvelope
mapping, using the literal RFI-214 field values from
docs/05_Downstream_Reference_Execution_Trace.md / RES's own
seed/meridian_tower.py, with RES's *real* response shape (numeric IDs
resolved to strings by the caller, per client/res_client.py's
resolve_rfi_references — not the illustrative trace's embedded-string
shape)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from client.res_client import ResolvedRFI
from mapper.rfi_mapper import map_rfi_to_envelope
from repository.connector_configuration_repository import ConnectorConfiguration

CONFIG = ConnectorConfiguration(
    connection_id="conn_res_meridian",
    project_id="proj_meridian_tower",
    source_system="procore",
    base_url="http://reference-engineering-backend:8000",
    oauth_token_url="http://reference-engineering-backend:8000/oauth/token",
    oauth_client_id="downstream-partial",
    oauth_client_secret="partial-scope-secret",
    granted_scope=["rfis", "submittals", "documents"],
    integration_tier="read_only",
    webhook_secret="seed-webhook-secret",
)

RFI_214 = {
    "id": 4821356,
    "project_id": 1,
    "number": "214",
    "display_number": "RFI-214",
    "subject": "Duct routing conflict at Grid B-4 vs. structural beam",
    "question": None,
    "response": "Reroute duct per attached SK-14...",
    "status": "CLOSED",
    "ball_in_court": "manager:1",
    "cost_impact_flag": None,
    "cost_code": None,
    "discipline_code": "M",
    "spawned_change_id": None,
    "raw_document_ref": "engineering://attachments/SK-14_reroute.pdf",
    "drawing_version_ids": [7],
    "spec_section_ids": [3],
    "location_ids": [4],
    "closed_at": "2026-07-28T09:14:03+00:00",
}


def _resolved(**overrides) -> ResolvedRFI:
    defaults = dict(
        res_project_id=1,
        rfi=RFI_214,
        spec_section_numbers=["23 31 13"],
        drawing_refs=[("M-2.1", "Rev C")],
        location_names=["Grid B-4"],
    )
    defaults.update(overrides)
    return ResolvedRFI(**defaults)


def test_maps_source_id_and_display_number():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.source_id == "4821356"
    assert envelope.display_number == "RFI-214"


def test_maps_type_to_rfi_approved():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.type == "RFI_APPROVED"


def test_maps_spec_section_and_location_refs():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.spec_section_refs == ["23 31 13"]
    assert envelope.location_refs == ["Grid B-4"]


def test_maps_drawing_refs_as_item_id_version_id_pairs():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert len(envelope.drawing_refs) == 1
    assert envelope.drawing_refs[0].item_id == "M-2.1"
    assert envelope.drawing_refs[0].version_id == "Rev C"


def test_maps_occurred_at_from_closed_at():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.occurred_at == datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)


def test_acting_credential_scope_is_partial_for_partial_scope_config():
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.acting_credential_scope == "partial:[documents,rfis,submittals]"


def test_acting_credential_scope_is_full_for_full_scope_config():
    full_config = ConnectorConfiguration(**{**CONFIG.__dict__, "granted_scope": ["*"]})
    envelope = map_rfi_to_envelope(_resolved(), full_config)
    assert envelope.acting_credential_scope == "full"


def test_region_is_none_not_fabricated():
    """RES has no region concept anywhere in its API — recorded deviation
    from docs/05's illustrative 'us-east' value (client/res_client.py
    module docstring, point 3)."""
    envelope = map_rfi_to_envelope(_resolved(), CONFIG)
    assert envelope.region is None


def test_raises_on_non_closed_rfi():
    open_rfi = {**RFI_214, "status": "OPEN"}
    with pytest.raises(ValueError, match="Expected a CLOSED RFI"):
        map_rfi_to_envelope(_resolved(rfi=open_rfi), CONFIG)


def test_raises_on_missing_closed_at():
    no_closed_at = {**RFI_214, "closed_at": None}
    with pytest.raises(ValueError, match="no closed_at timestamp"):
        map_rfi_to_envelope(_resolved(rfi=no_closed_at), CONFIG)
