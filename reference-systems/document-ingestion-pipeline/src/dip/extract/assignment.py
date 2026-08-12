"""Deterministic cell assignment — every OCR word is assigned to the grid
cell (row, col) whose ruled boundaries contain its centroid. No clustering
epsilon, no statistical inference: a word's centroid either falls inside a
cell's rectangle or it doesn't.

Engine-agnostic on purpose (decision 8): this module consumes
dip.ocr.engines.base.OcrWord, the shared shape both Tesseract and RapidOCR
already produce — nothing here imports pytesseract or rapidocr_onnxruntime,
or relies on Tesseract's block/par/line hierarchy (that hierarchy is used
only as a supporting cross-check in build.py, never a hard dependency here).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from dip.ocr.engines.base import OcrWord
from dip.tablegrid.models import TableGrid


@dataclass(frozen=True)
class CellAssignment:
    row: int
    col: int
    words: tuple[OcrWord, ...]


def _locate_index(boundaries: list[float], value: float) -> int | None:
    """Which [boundaries[i], boundaries[i+1]) bucket value falls in, or
    None if value is outside every bucket."""
    i = bisect.bisect_right(boundaries, value) - 1
    if i < 0 or i >= len(boundaries) - 1:
        return None
    return i


def assign_words_to_cells(grid: TableGrid, words: list[OcrWord]) -> dict[tuple[int, int], list[OcrWord]]:
    """Assign each word to exactly one (row, col) cell by its box centroid.
    A word whose centroid falls outside the grid entirely (e.g. title-block
    text above the table) is silently excluded from the returned map — it
    was never part of this table, not a data-loss bug."""
    cells: dict[tuple[int, int], list[OcrWord]] = {}

    for word in words:
        cx = word.left + word.width / 2.0
        cy = word.top + word.height / 2.0

        row = _locate_index(grid.row_boundaries, cy)
        col = _locate_index(grid.col_boundaries, cx)
        if row is None or col is None:
            continue

        cells.setdefault((row, col), []).append(word)

    return cells
