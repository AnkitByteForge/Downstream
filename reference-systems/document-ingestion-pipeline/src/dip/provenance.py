"""EvidenceRef — the one provenance shape every extracted fact in DIP carries.

Per the approved plan: "every extracted fact/change must remain traceable to
document, page, optional bounding box, extraction method, extractor version,
timestamp." This module exists so that guarantee is enforced by the type
system in one place, not re-implemented per module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExtractionMethod = Literal[
    "native_text",
    "raster_ocr",
    "vector_curve_ocr",
    "synthetic_fixture",
]


class BoundingBox(BaseModel):
    """Pixel-space bounding box on a rendered page image. Optional — native
    text extraction may have no useful box; OCR word boxes always have one."""

    model_config = ConfigDict(frozen=True)

    left: float
    top: float
    right: float
    bottom: float


class EvidenceRef(BaseModel):
    """A pointer back to exactly where an extracted fact came from.

    Never a copy of the source document, never a paraphrase — a pointer,
    per the same discipline the frozen Downstream architecture already
    requires of `raw_document_ref` (docs/03's storage-boundaries table).
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, description="sha256 of the source file's bytes.")
    file_name: str = Field(min_length=1)
    page_index: int = Field(ge=0, description="0-indexed page number within the document.")
    page_label: str | None = Field(
        default=None,
        description="Human-facing sheet/section label if resolvable (e.g. from a PDF bookmark).",
    )
    bounding_box: BoundingBox | None = None
    extraction_method: ExtractionMethod
    extractor_version: str = Field(min_length=1)
    extracted_at: datetime
    ocr_engine: str | None = Field(
        default=None,
        description=(
            "Which OCR engine produced this fact ('tesseract', 'rapidocr'), if any. "
            "None for native_text/synthetic_fixture extraction, where no OCR engine "
            "was involved. Optional and defaulted for backward compatibility with "
            "every EvidenceRef constructed before Phase C (docs/adr-equivalent: "
            "Phase C decision 11) — existing Phase A/B/D fixtures and artifacts "
            "validate unchanged."
        ),
    )


class FieldProvenance(BaseModel):
    """Per-field confidence, kept as two separate numbers per the Phase C
    design — never combined, averaged, or multiplied into one score.

    ocr_confidence answers "how confidently was this text recognized?"
    (the OCR engine's own reported score for the word(s) this field's value
    came from). extraction_confidence answers "how confidently was this
    word/cell assigned to this field?" (a property of the table-reconstruction
    step — ruling-line boundary clarity and cell-assignment ambiguity — and is
    computed independently of how confidently the OCR engine read the text).

    This is deliberately NOT Downstream's CERTAIN/PROBABLE/POSSIBLE reasoning
    tier (docs/reference/Downstream_Intelligence_Specification.md §7) — that
    tier is computed later, from graph evidence, by the Reasoning Pipeline,
    and is out of DIP's scope entirely.
    """

    model_config = ConfigDict(frozen=True)

    ocr_confidence: float | None = Field(
        default=None, description="The OCR engine's own reported confidence for the source word(s), 0-100."
    )
    extraction_confidence: float | None = Field(
        default=None,
        description="How confidently the table-reconstruction step assigned that text to this field's cell, 0-100.",
    )
    evidence: EvidenceRef
