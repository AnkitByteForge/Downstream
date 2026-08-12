"""Phase A data contracts — Document and PageManifestEntry.

Pydantic, matching the convention already established by packages/* in the
root Downstream repo. These are DIP-owned; nothing here is a Downstream or
RES entity (see docs/architecture/DSH_Ingestion_Pipeline_Architecture.md §1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PageClassification = Literal["native_text", "raster_embedded", "vector_curve", "mixed"]


class Document(BaseModel):
    """One immutable source PDF, identified by the hash of its own bytes —
    never by filename alone, so a silently-replaced file is never mistaken
    for the one already manifested."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1, description="sha256 of the file's bytes.")
    file_name: str = Field(min_length=1)
    page_count: int = Field(ge=0)
    pdf_version: int | None = Field(default=None, description="e.g. 17 for PDF 1.7, per pypdfium2.get_version().")
    file_size_bytes: int = Field(ge=0)
    manifest_built_at: datetime
    extractor_version: str = Field(min_length=1)


class PageManifestEntry(BaseModel):
    """Per-page facts derived from page-object/text-layer inspection only —
    never from rendering. classification/needs_ocr are heuristic, not
    validated ground truth (see dip.config's threshold constants)."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1)
    page_index: int = Field(ge=0)
    char_len: int = Field(ge=0, description="Native text-layer character count.")
    image_coverage_pct: float = Field(ge=0, le=100)
    path_object_count: int = Field(ge=0)
    classification: PageClassification
    needs_ocr: bool
    bookmark_title: str | None = Field(
        default=None,
        description="First PDF outline/bookmark entry pointing at this page, if any.",
    )
    extraction_method: Literal["native_text"] = "native_text"
    extractor_version: str = Field(min_length=1)
    extracted_at: datetime
