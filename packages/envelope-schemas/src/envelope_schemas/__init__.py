"""Canonical connector envelopes.

Every Connector adapter (Procore, SAP, ACC, Oracle, ERPNext, the generic
email adapter, ...) normalizes whatever native payload it receives into one
of exactly two canonical envelopes before anything else in the system ever
sees it. See docs/03_Downstream_Systems_Architecture.md §1 and
docs/04_Downstream_Connector_Layer_Validation.md for the field-by-field
justification of every field below.
"""

from envelope_schemas.commercial_artifact_snapshot import (
    ArtifactType,
    CommercialArtifactSnapshot,
    CostCodeFormat,
    DataFreshnessPath,
    OrgScope,
)
from envelope_schemas.engineering_event_envelope import (
    DrawingRef,
    EngineeringEventEnvelope,
    EngineeringEventType,
)

__all__ = [
    "ArtifactType",
    "CommercialArtifactSnapshot",
    "CostCodeFormat",
    "DataFreshnessPath",
    "DrawingRef",
    "EngineeringEventEnvelope",
    "EngineeringEventType",
    "OrgScope",
]
