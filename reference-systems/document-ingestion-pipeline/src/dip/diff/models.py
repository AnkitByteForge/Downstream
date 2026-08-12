"""Phase D/C data contracts.

EquipmentRow's field set was corrected during Phase C's investigation
against the REAL E0.4 Air Handler Replacement Schedule (direct visual
inspection of the rendered sheet, not the earlier paraphrase). The real
table has three parallel electrical-characteristic blocks (Existing Unit
Supply Fan / Existing Unit Return Fan / New Unit); EquipmentRow v1 (this
model) covers identity plus the New Unit block only — the block describing
the equipment actually being installed, which is what a real revision would
change, and what Downstream_Intelligence_Specification.md §13's own
walkthrough and Downstream_Demo_Strategy.md's #1-ranked scenario are about.
Existing Supply Fan / Existing Return Fan / Conductors / Motor Controller /
Motor Disconnect / Notes are explicitly deferred, not extracted here.

`circuit_number` and `hp` were REMOVED from the original Phase D placeholder
— neither exists in the New Unit block (only in the two Existing blocks).
`conduit` was ADDED — it's a real New Unit column the placeholder missed.
This is a correction to the real source structure, not new invented
generality — see docs/architecture (Phase C investigation report) for the
full column inventory of all three blocks.

diff_schedule() in engine.py remains generic over any Pydantic row model
exposing the named key/compare fields — this correction doesn't touch it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from dip.provenance import EvidenceRef, FieldProvenance


class EquipmentRow(BaseModel):
    """One row of the E0.4 Air Handler Replacement Schedule's New Unit
    block, plus row identity. tag is the stable row key — equipment
    designation is what a diff matches revisions on, exactly as a real
    document-control process would.

    fla/mca are kept as raw/display strings (unchanged field names/types
    from the original Phase D placeholder, for backward compatibility with
    the existing synthetic fixtures and diff tests) — Phase C's numeric
    normalization (decision 12) lives in the separate fla_numeric/mca_numeric
    fields, which are null whenever the raw OCR text didn't parse cleanly,
    never a silently "fixed" guess.
    """

    model_config = ConfigDict(frozen=True)

    tag: str = Field(min_length=1, description="New Equipment Designation, e.g. 'AH-9C'.")
    existing_designation: str | None = None
    fed_from_panel: str | None = Field(default=None, description="New Unit block's Fed From Panel column.")
    breaker_rating: str | None = Field(default=None, description="New Unit block's Circuit Breaker Rating column.")
    conduit: str | None = Field(default=None, description="New Unit block's Conduit column.")
    volts: str | None = Field(default=None, description="New Unit block's Volts column.")
    fla: str | None = Field(default=None, description="New Unit block's FLA column, raw/display string.")
    mca: str | None = Field(default=None, description="New Unit block's MCA column, raw/display string.")

    fla_numeric: float | None = Field(
        default=None,
        description="Parsed numeric FLA. Null if the raw OCR text for `fla` didn't parse as a number — never a guessed/fixed value (decision 12).",
    )
    mca_numeric: float | None = Field(
        default=None,
        description="Parsed numeric MCA. Same null-on-failure rule as fla_numeric.",
    )
    mca_fla_suspicious: bool = Field(
        default=False,
        description=(
            "True when both fla_numeric and mca_numeric parsed but mca_numeric <= fla_numeric — "
            "real electrical convention is MCA > FLA. Flagged, never corrected (decision 13)."
        ),
    )
    tag_pattern_flag: bool = Field(
        default=False,
        description="True when `tag` does not match the AH-* pattern observed on this sheet. Advisory only, never rejects the row (decision 15).",
    )

    evidence: EvidenceRef
    field_provenance: dict[str, FieldProvenance] = Field(
        default_factory=dict,
        description=(
            "Per-New-Unit-field OCR + extraction confidence and evidence, keyed by field name "
            "('fed_from_panel', 'breaker_rating', 'conduit', 'volts', 'fla', 'mca'). `evidence` above "
            "is the row-identity (tag cell)'s own provenance; this map is each other field's own, "
            "which may legitimately differ (decisions 9/10)."
        ),
    )


class FieldChange(BaseModel):
    """One field-level difference on a matched row."""

    model_config = ConfigDict(frozen=True)

    field: str
    before: str | None
    after: str | None


class RowChange(BaseModel):
    """All field-level changes for one matched row key."""

    model_config = ConfigDict(frozen=True)

    key: str
    change_type: Literal["added", "removed", "changed"]
    fields: list[FieldChange] = Field(default_factory=list)
    before_evidence: EvidenceRef | None = None
    after_evidence: EvidenceRef | None = None


class DetectedChange(BaseModel):
    """The full result of diffing two revisions of the same sheet/table."""

    model_config = ConfigDict(frozen=True)

    sheet: str
    key_field: str
    row_changes: list[RowChange] = Field(default_factory=list)
    unchanged_row_count: int = Field(ge=0)
    summary: str
