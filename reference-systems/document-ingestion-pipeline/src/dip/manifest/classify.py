"""Page classification heuristic — pure, no I/O, no PDF dependency.

Thresholds live in dip.config, not here, so they can be tuned without
touching logic. Deliberately conservative: an ambiguous page is classified
"mixed" and flagged needs_ocr=True rather than silently assumed to be fine —
per the "no silent corruption" requirement, a false "needs OCR" is a wasted
benchmark page, but a false "no OCR needed" is a lost fact.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dip import config
from dip.manifest.models import PageClassification


class PageStats(BaseModel):
    """The three raw signals classify_page reasons over."""

    model_config = ConfigDict(frozen=True)

    char_len: int = Field(ge=0)
    image_coverage_pct: float = Field(ge=0, le=100)
    path_object_count: int = Field(ge=0)


def classify_page(stats: PageStats) -> tuple[PageClassification, bool]:
    """Return (classification, needs_ocr).

    Mirrors the three failure/success modes documented empirically in
    docs/research/DSH_Atascadero_Reconnaissance.md §1-2:
      1. native text schedule -> plenty of char_len, low image/path -> native_text
      2. raster-image schedule embedded in a vector sheet -> high image_coverage_pct -> raster_embedded
      3. text-drawn-as-vector-curves -> near-zero char_len, huge path_object_count -> vector_curve
    """
    if (
        stats.image_coverage_pct >= config.CLASSIFY_RASTER_IMAGE_COVERAGE_PCT
    ):
        return "raster_embedded", True

    if (
        stats.path_object_count >= config.CLASSIFY_VECTOR_CURVE_PATH_OBJECT_COUNT
        and stats.char_len < config.CLASSIFY_VECTOR_CURVE_MAX_TEXT_CHARS
    ):
        return "vector_curve", True

    if (
        stats.char_len >= config.CLASSIFY_MIN_NATIVE_TEXT_CHARS
        and stats.path_object_count < config.CLASSIFY_VECTOR_CURVE_PATH_OBJECT_COUNT
    ):
        return "native_text", False

    return "mixed", True
