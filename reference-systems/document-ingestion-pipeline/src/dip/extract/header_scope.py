"""Locates the New Unit block's columns by matching real header text — never
hardcoded absolute column indices. The full detected grid carries more
columns (35) than the New Unit block alone needs, and the source of the
extra columns elsewhere in the grid was not fully diagnosed (see
dip.tablegrid.grid's module docstring); anchoring on real header text is
robust to that uncertainty, a fixed-position mapping would not be.

Anchors, both confirmed unique/duplicate by direct visual inspection of the
real E0.4 header during the Phase C investigation:
  - "CONDUIT" appears exactly once, only in the New Unit block.
  - "DESIGNATION" appears exactly twice — New Equipment Designation (left)
    and Existing Equipment Designation (right of it).
The New Unit block's own column order, left to right, per that same visual
inspection: FLA, MCA, Volts, [Fed From] Panel, [Circuit] Breaker Rating,
Conduit — so every other New Unit column is located relative to CONDUIT's
column index, not by its own independent text match (several of these
labels, e.g. "FLA"/"MCA"/"PANEL", repeat elsewhere in the Existing Supply/
Return Fan blocks and would be ambiguous to match directly).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from dip.ocr.engines.base import OcrWord
from dip.tablegrid.models import TableGrid


class HeaderScopeError(ValueError):
    """Raised when the expected header anchor text isn't found on this
    page/grid — never falls back to a guessed column position."""


@dataclass(frozen=True)
class NewUnitColumnMap:
    tag_col: int
    existing_designation_col: int
    fla_col: int
    mca_col: int
    volts_col: int
    fed_from_panel_col: int
    breaker_rating_col: int
    conduit_col: int


def header_region_text_by_column(
    grid: TableGrid, header_words: list[OcrWord]
) -> dict[int, str]:
    """Concatenates header-region OCR word text per column bucket. Header
    words sit above grid.row_boundaries[0] (the header row(s) are not part
    of the detected data-row band at all — confirmed by direct visual
    inspection: the header sits in the gap above the first ruled data row),
    so only column lookup applies here, never row lookup."""
    text_by_col: dict[int, list[str]] = {}
    for word in header_words:
        cx = word.left + word.width / 2.0
        i = bisect.bisect_right(grid.col_boundaries, cx) - 1
        if i < 0 or i >= grid.n_cols:
            continue
        text_by_col.setdefault(i, []).append(word.text)
    return {col: " ".join(words).upper() for col, words in text_by_col.items()}


def locate_new_unit_columns(grid: TableGrid, header_words: list[OcrWord]) -> NewUnitColumnMap:
    text_by_col = header_region_text_by_column(grid, header_words)

    conduit_cols = sorted(c for c, t in text_by_col.items() if "CONDUIT" in t)
    if len(conduit_cols) != 1:
        raise HeaderScopeError(
            f"Expected exactly one column matching 'CONDUIT' (New Unit block anchor), "
            f"found {len(conduit_cols)}: {conduit_cols}"
        )
    conduit_col = conduit_cols[0]

    designation_cols = sorted(c for c, t in text_by_col.items() if "DESIGNATION" in t)
    if len(designation_cols) < 2:
        raise HeaderScopeError(
            f"Expected at least two columns matching 'DESIGNATION' (identity columns), "
            f"found {len(designation_cols)}: {designation_cols}"
        )
    tag_col, existing_designation_col = designation_cols[0], designation_cols[1]

    if conduit_col - 5 < 0:
        raise HeaderScopeError(
            f"CONDUIT anchor at column {conduit_col} leaves no room for the five "
            f"New Unit columns expected to its left."
        )

    return NewUnitColumnMap(
        tag_col=tag_col,
        existing_designation_col=existing_designation_col,
        fla_col=conduit_col - 5,
        mca_col=conduit_col - 4,
        volts_col=conduit_col - 3,
        fed_from_panel_col=conduit_col - 2,
        breaker_rating_col=conduit_col - 1,
        conduit_col=conduit_col,
    )
