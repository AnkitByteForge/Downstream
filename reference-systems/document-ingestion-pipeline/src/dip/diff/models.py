"""Phase D data contracts.

EquipmentRow's fields are taken directly from the real E0.4 Air Handler
Replacement Schedule columns already read (both by the reconnaissance
report's human inspection and by this implementation's own Phase B OCR
smoke test) — New/Existing Equipment Designation, Fed From Panel, Circuit
Number, Circuit Breaker Rating, Volts, HP, FLA, MCA.

Per the approved plan: EquipmentRow is the *first extraction target only* —
not a frozen universal ingestion model. diff_schedule() in engine.py is
deliberately generic over any Pydantic row model exposing the named key/
compare fields, so a future panel-schedule or one-line-diagram row type can
reuse the same diff mechanism without EquipmentRow needing to grow fields it
doesn't own.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from dip.provenance import EvidenceRef


class EquipmentRow(BaseModel):
    """One row of an AHU-schedule-family table. tag is the stable row key —
    equipment designation is what a diff matches revisions on, exactly as a
    real document-control process would."""

    model_config = ConfigDict(frozen=True)

    tag: str = Field(min_length=1, description="New Equipment Designation, e.g. 'AH-9C'.")
    existing_designation: str | None = None
    fed_from_panel: str | None = None
    circuit_number: str | None = None
    breaker_rating: str | None = None
    volts: str | None = None
    hp: str | None = None
    fla: str | None = None
    mca: str | None = None
    evidence: EvidenceRef


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
