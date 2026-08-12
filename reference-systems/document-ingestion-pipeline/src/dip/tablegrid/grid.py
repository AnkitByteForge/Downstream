"""Ruling-line grid detection — a deterministic projection-profile technique
(classical document image analysis, not ML), chosen because the real E0.4
sheet has visible drawn table borders (confirmed by direct visual inspection
during the Phase C investigation), which is a far more reliable source of
column/row boundaries than statistically clustering noisy OCR word-box
coordinates.

Algorithm:
    1. Binarize the rendered page (dark-ink vs. background) — safe here
       because these are crisp, born-digital renders with a strongly
       bimodal pixel histogram, not scanned images with noise to fight
       (see dip.config's threshold constants and their calibration note).
    2. Row-wise darkness projection -> candidate horizontal ruling lines
       (a genuine printed rule spans nearly the full row width, giving a
       much higher density than even a dense line of small text).
    3. Keep the longest contiguous run of *regularly spaced* horizontal
       boundaries — the real table's row band, as distinct from sparse,
       unrelated lines elsewhere on the page (title-block borders, etc.).
    4. Column-wise darkness projection, restricted to that row band's
       vertical extent, -> vertical ruling lines.

Known limitation, measured not assumed (see the implementation report):
on the real E0.4 sheet, this detects the table's first ~59 data rows
(y in [458, 2231] at render scale 2.0) but not the remainder of the visible
table (which continues to roughly y=3200) — row-density measured directly
in that lower region drops below the detection floor almost everywhere,
with only two isolated spikes too far apart (~150px) to join the "regular
band." The root cause was not fully diagnosed (a plausible explanation is a
lighter rule-line weight in that portion of the source CAD drawing) and is
left as documented, deferred follow-up work, not silently masked. The v1
vertical slice (AH-9C plus the 8-row ground-truth sample) is entirely
within the successfully-detected band, so this does not block Phase C v1.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from dip import config
from dip.tablegrid.models import TableGrid


class GridDetectionError(ValueError):
    """Raised when no table-like ruling-line structure is found. Never
    silently returns a fabricated/guessed grid."""


def _dark_mask(image: Image.Image) -> np.ndarray:
    gray = np.array(image.convert("L"))
    return gray < config.GRID_DARK_PIXEL_THRESHOLD


def _candidate_boundaries_1d(density: np.ndarray, min_density: float, merge_gap: int) -> list[float]:
    """Contiguous runs of density >= min_density, each merged into one
    boundary at its midpoint."""
    candidate_indices = np.where(density >= min_density)[0]
    if len(candidate_indices) == 0:
        return []

    boundaries: list[float] = []
    run_start = candidate_indices[0]
    prev = candidate_indices[0]
    for idx in candidate_indices[1:]:
        if idx - prev > merge_gap:
            boundaries.append((run_start + prev) / 2.0)
            run_start = idx
        prev = idx
    boundaries.append((run_start + prev) / 2.0)
    return boundaries


def _longest_regular_band(boundaries: list[float], max_pitch: float) -> list[float]:
    """The longest contiguous sub-sequence of `boundaries` where every
    consecutive gap is <= max_pitch — the real table's densely, regularly
    ruled row band, distinguished from sparse unrelated lines elsewhere on
    the page."""
    if not boundaries:
        return []

    best_run: list[float] = [boundaries[0]]
    current_run: list[float] = [boundaries[0]]
    for prev, curr in zip(boundaries, boundaries[1:]):
        if curr - prev <= max_pitch:
            current_run.append(curr)
        else:
            if len(current_run) > len(best_run):
                best_run = current_run
            current_run = [curr]
    if len(current_run) > len(best_run):
        best_run = current_run
    return best_run


def detect_grid(
    image: Image.Image,
    document_id: str,
    page_index: int,
    render_scale: float,
) -> TableGrid:
    """Detect the row/column ruling-line grid on one rendered page.

    Raises GridDetectionError if no regular table-like row band, or no
    column boundaries within it, are found — this function never returns a
    guessed/fabricated grid.
    """
    dark = _dark_mask(image)

    row_density = dark.mean(axis=1)
    all_row_boundaries = _candidate_boundaries_1d(
        row_density, config.GRID_MIN_ROW_LINE_DENSITY, config.GRID_LINE_MERGE_GAP_PX
    )
    row_band = _longest_regular_band(all_row_boundaries, config.GRID_MAX_ROW_PITCH_PX)
    if len(row_band) < 3:
        raise GridDetectionError(
            f"No regular ruling-line row band found on page {page_index} "
            f"(longest regular run had {len(row_band)} boundaries, need >= 3 for >= 2 rows)."
        )

    top, bottom = row_band[0], row_band[-1]
    column_region = dark[int(top) : int(bottom) + 1, :]
    col_density = column_region.mean(axis=0)
    col_boundaries = _candidate_boundaries_1d(
        col_density, config.GRID_MIN_COLUMN_LINE_DENSITY, config.GRID_LINE_MERGE_GAP_PX
    )
    if len(col_boundaries) < 2:
        raise GridDetectionError(
            f"No vertical ruling-line boundaries found within the detected row band "
            f"on page {page_index} (found {len(col_boundaries)}, need >= 2 for >= 1 column)."
        )

    return TableGrid(
        document_id=document_id,
        page_index=page_index,
        render_scale=render_scale,
        row_boundaries=row_band,
        col_boundaries=col_boundaries,
    )
