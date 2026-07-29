"""CommercialArtifactSnapshot — the canonical shape every Commercial
Connector (SAP, Oracle, Procore Commitments, ERPNext, ...) normalizes a
purchase order / vendor / delivery's current state into.

Base shape: docs/03_Downstream_Systems_Architecture.md §1.
The three additions (org_scope, cost_code_format, data_freshness_path) come
from the real-system validation in
docs/04_Downstream_Connector_Layer_Validation.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ArtifactType = Literal["PO", "VENDOR", "DELIVERY"]

# Values named in docs/04_Downstream_Connector_Layer_Validation.md's envelope
# synthesis: "CSI MasterFormat | SAP WBS | Oracle Project/Task | ERPNext Cost
# Center | Customer-defined" — snake/upper-cased here for a stable wire enum.
CostCodeFormat = Literal[
    "CSI_MASTERFORMAT",
    "SAP_WBS",
    "ORACLE_PROJECT_TASK",
    "ERPNEXT_COST_CENTER",
    "CUSTOMER_DEFINED",
]

# Named in docs/07_Downstream_Implementation_Blueprint.md §6's
# artifact_snapshots table comment: "real_time_event|polled|bulk_import".
DataFreshnessPath = Literal["real_time_event", "polled", "bulk_import"]


class OrgScope(BaseModel):
    """Generalizes SAP's Company Code/Plant and Oracle's Business Unit.

    Without this, the same PO number can collide across org units in any
    real enterprise landscape (docs/04, envelope synthesis section). All
    fields are optional because which of them applies is itself a function
    of `source_system` — SAP populates company_code/plant, Oracle populates
    business_unit, and a system with no such dimension (e.g. ERPNext in
    stock form) populates none.
    """

    model_config = ConfigDict(frozen=True)

    company_code: str | None = None
    plant: str | None = None
    business_unit: str | None = None


class CommercialArtifactSnapshot(BaseModel):
    """The canonical, source-agnostic, point-in-time state of one Commercial
    Artifact (a Purchase Order, Vendor, or Delivery/Schedule Activity), as
    read from the connected commercial system of record.

    This is what `fetchArtifactSnapshot` on the Connector Interface returns —
    never a raw SAP OData row or Oracle REST payload.
    """

    model_config = ConfigDict(frozen=True)

    envelope_type: Literal["CommercialArtifactSnapshot"] = "CommercialArtifactSnapshot"

    source_system: str = Field(
        min_length=1,
        description="The originating commercial system, e.g. 'sap', 'oracle', 'procore'.",
    )
    source_id: str = Field(
        min_length=1,
        description="The source system's real identifier for this artifact (e.g. SAP's 10-digit PO number).",
    )
    artifact_type: ArtifactType

    cost_code: str | None = None
    cost_code_format: CostCodeFormat | None = Field(
        default=None,
        description=(
            "Which of the (at least) five real cost-code shapes `cost_code` is "
            "in, so the Graph Layer's key-matching applies the correct normalizer."
        ),
    )

    spec_section_refs: list[str] = Field(default_factory=list)

    lifecycle_position: str | None = Field(
        default=None,
        description=(
            "The artifact's current lifecycle stage, read directly from the "
            "connected commercial system, never invented by Downstream. The "
            "frozen docs use two different vocabularies for this field across "
            "narrative levels — product-level (draft / issued / in fabrication / "
            "shipped / installed) and the Reference Trace's connector-level "
            "values (e.g. SCHEDULED, IN_FABRICATION, SHIPPED, N/A) — so this is "
            "intentionally left as a free-form string rather than a Literal "
            "enum, to avoid asserting a single canonical casing neither "
            "document actually commits to."
        ),
    )

    value: float | None = Field(
        default=None,
        description="The artifact's value, in whatever currency the source system reports it in.",
    )
    vendor_ref: str | None = None
    project_ref: str = Field(min_length=1)

    org_scope: OrgScope | None = None
    data_freshness_path: DataFreshnessPath | None = Field(
        default=None,
        description=(
            "How this snapshot arrived: a real-time event, a poll, or a "
            "one-time bulk import. A polled SAP snapshot and a webhook-pushed "
            "snapshot are not equally trustworthy, and Confidence Tiering "
            "should be able to tell the difference."
        ),
    )

    fetched_at: datetime | None = Field(
        default=None,
        description="When this snapshot was fetched from the source system.",
    )
