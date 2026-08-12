"""E.0 — the persistent structured_state snapshot.

A StructuredStateSnapshot is one immutable extraction run's full output:
every EquipmentRow (every field, every validation status — VALID,
AMBIGUOUS, INVALID, and MISSING alike, unfiltered), plus the run-level
identity that distinguishes one persisted snapshot from another. Per the
approved DIP -> Engineering Evidence Promotion plan (§2/§3), this is still
"Extracted Engineering Evidence" — DIP-owned, not RES-owned, and not yet
filtered down to "Validated Engineering Fact" (that's E.1, a derived read
over this snapshot, never a second file — see dip.promote.filter).

render_scale lives here, on the snapshot, rather than being added to
EquipmentRow/EvidenceRef: it is a property of one extraction *run*
(identical for every row that run produced), not a property of any
individual field, so adding it to the row model would touch Phase C's
already-approved, frozen-for-this-milestone row shape for no new
information. Likewise ocr_engine here records the *primary* engine used
for the run — a field's own possibly-different fallback-engine reading is
already preserved unchanged on that field's own
FieldProvenance.evidence.ocr_engine, untouched by this addition.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from dip.diff.models import EquipmentRow


class StructuredStateSnapshot(BaseModel):
    """One persisted extraction run. Frozen — a snapshot is never edited in
    place; a different extraction run (different extractor_version,
    ocr_engine, or render_scale) is a different, independently-kept
    snapshot, per the approved plan's versioning/reprocessing strategy."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, description="sha256 of the source file's bytes.")
    file_name: str = Field(min_length=1)
    page_index: int = Field(ge=0)
    page_label: str

    extractor_version: str = Field(min_length=1)
    ocr_engine: str = Field(min_length=1, description="The primary OCR engine used for this extraction run.")
    render_scale: float = Field(gt=0)
    extracted_at: datetime

    rows: list[EquipmentRow] = Field(
        default_factory=list,
        description="Every extracted row, every field, every validation status — unfiltered evidence.",
    )
