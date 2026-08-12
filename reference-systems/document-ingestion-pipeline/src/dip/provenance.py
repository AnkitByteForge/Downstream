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
