"""Table-grid data contracts.

A TableGrid is nothing but a set of pixel-space row/column boundary
coordinates on one rendered page — the deterministic, ruling-line-derived
structure that OCR word boxes get assigned into (dip.extract.assignment),
never itself carrying recognized text.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TableGrid(BaseModel):
    """Row/column boundaries detected on one rendered page, in pixel space.

    `row_boundaries`/`col_boundaries` are sorted, ascending pixel
    coordinates — N boundaries describe N-1 cells along that axis. Both are
    a property of one specific (document_id, page_index, render_scale)
    combination; a grid detected at one scale is not valid at another.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1)
    page_index: int = Field(ge=0)
    render_scale: float
    row_boundaries: list[float] = Field(min_length=2, description="Ascending pixel y-coordinates; N-1 rows.")
    col_boundaries: list[float] = Field(min_length=2, description="Ascending pixel x-coordinates; N-1 columns.")

    @property
    def n_rows(self) -> int:
        return len(self.row_boundaries) - 1

    @property
    def n_cols(self) -> int:
        return len(self.col_boundaries) - 1

    def cell_bounds(self, row: int, col: int) -> tuple[float, float, float, float]:
        """Returns (left, top, right, bottom) for one (row, col) cell."""
        return (
            self.col_boundaries[col],
            self.row_boundaries[row],
            self.col_boundaries[col + 1],
            self.row_boundaries[row + 1],
        )
