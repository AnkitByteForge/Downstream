"""EngineeringEventEnvelope — the canonical shape every Engineering Connector
(Procore, ACC, ...) normalizes an RFI approval / drawing revision / spec
update into.

Base shape: docs/03_Downstream_Systems_Architecture.md §1.
The four additions (display_number, split item_id/version_id, region,
acting_credential_scope) come from the real-system validation in
docs/04_Downstream_Connector_Layer_Validation.md, and the exact wire shape
below (including the `envelope_type` discriminator) matches Phase 1.3 of
docs/05_Downstream_Reference_Execution_Trace.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EngineeringEventType = Literal["RFI_APPROVED", "DRAWING_REVISED", "SPEC_UPDATED"]


class DrawingRef(BaseModel):
    """A reference to one version of one drawing/document item.

    item_id and version_id are kept as two distinct fields, never collapsed
    into one opaque string — per the Connector Layer Validation, ACC's whole
    revision-diffing capability (and, generally, the ability to tell "Rev B"
    from "Rev C") depends on this split.
    """

    model_config = ConfigDict(frozen=True)

    item_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)


class EngineeringEventEnvelope(BaseModel):
    """The canonical, source-agnostic shape of one detected engineering
    change.

    This is the only place a raw Procore/ACC/etc. payload is ever touched —
    every Engineering Connector adapter's mapper layer (apps/connector-*/src/mapper/)
    is responsible for producing exactly this shape from whatever thin
    webhook plus enrichment GET-back its source system gives it. Nothing
    downstream of this envelope is allowed to see a raw source-system payload.
    """

    model_config = ConfigDict(frozen=True)

    envelope_type: Literal["EngineeringEventEnvelope"] = "EngineeringEventEnvelope"

    source_system: str = Field(
        min_length=1,
        description="The originating engineering system, e.g. 'procore', 'acc'.",
    )
    source_id: str = Field(
        min_length=1,
        description=(
            "The source system's real, opaque primary key for this resource "
            "(e.g. Procore's numeric RFI id). Never the editable human-facing number."
        ),
    )
    display_number: str | None = Field(
        default=None,
        description=(
            "The editable, human-facing label (e.g. 'RFI-214'). Cosmetic only — "
            "never used as a key downstream of the connector."
        ),
    )
    type: EngineeringEventType

    spec_section_refs: list[str] = Field(default_factory=list)
    drawing_refs: list[DrawingRef] = Field(default_factory=list)
    location_refs: list[str] = Field(default_factory=list)

    raw_document_ref: str | None = Field(
        default=None,
        description=(
            "A pointer to the source document in the origin system "
            "(e.g. 'procore://attachments/991211'). Never a copy of the document."
        ),
    )

    region: str | None = Field(
        default=None,
        description="Endpoint/data-residency region (e.g. 'us-east'), for correct, replay-safe routing.",
    )
    acting_credential_scope: str | None = Field(
        default=None,
        description=(
            "What the fetching credential could actually see at fetch time "
            "(e.g. 'partial:[rfis,submittals,documents]' or 'full'). Without this, "
            "a Certain confidence tier from an under-scoped fetch is indistinguishable "
            "from a genuinely certain one."
        ),
    )

    occurred_at: datetime
