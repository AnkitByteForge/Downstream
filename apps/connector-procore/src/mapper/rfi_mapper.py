"""raw RES RFI payload -> EngineeringEventEnvelope.

This is the only place a raw RES/Procore-shaped payload is ever touched
(envelope_schemas.EngineeringEventEnvelope's own docstring): everything
downstream of this module only ever sees the canonical envelope.
"""

from __future__ import annotations

from datetime import datetime

from envelope_schemas import DrawingRef, EngineeringEventEnvelope

from client.res_client import ResolvedRFI
from repository.connector_configuration_repository import ConnectorConfiguration


def _acting_credential_scope_wire_value(granted_scope: list[str]) -> str:
    """Mirrors RES's own PermissionScope.as_wire_value() format
    ('partial:[documents,rfis,submittals]' or 'full') so the value on the
    envelope reads identically to how RES itself would describe the same
    scope."""
    if "*" in granted_scope:
        return "full"
    return "partial:[" + ",".join(sorted(granted_scope)) + "]"


def map_rfi_to_envelope(resolved: ResolvedRFI, config: ConnectorConfiguration) -> EngineeringEventEnvelope:
    rfi = resolved.rfi
    if rfi["status"] != "CLOSED":
        raise ValueError(
            f"Expected a CLOSED RFI (RES only dispatches its 'rfis'/'update' webhook on close "
            f"transitions, per application/use_cases/rfi_use_cases.py CloseRFI), got status={rfi['status']!r}"
        )
    if rfi["closed_at"] is None:
        raise ValueError(f"RFI {rfi['id']} is CLOSED but has no closed_at timestamp")

    return EngineeringEventEnvelope(
        source_system=config.source_system,
        source_id=str(rfi["id"]),
        display_number=rfi["display_number"],
        type="RFI_APPROVED",
        spec_section_refs=resolved.spec_section_numbers,
        drawing_refs=[
            DrawingRef(item_id=sheet_number, version_id=revision_label)
            for sheet_number, revision_label in resolved.drawing_refs
        ],
        location_refs=resolved.location_names,
        raw_document_ref=rfi.get("raw_document_ref"),
        # RES models a single, non-regional deployment — no region concept
        # exists anywhere in its API (verified: no `region` field on any
        # resource). Left null rather than fabricating a value like the
        # illustrative trace's "us-east": there is nothing real to put here.
        region=None,
        acting_credential_scope=_acting_credential_scope_wire_value(config.granted_scope),
        occurred_at=datetime.fromisoformat(rfi["closed_at"]) if isinstance(rfi["closed_at"], str) else rfi["closed_at"],
    )
