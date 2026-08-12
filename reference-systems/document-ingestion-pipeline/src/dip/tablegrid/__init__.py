"""Phase C — deterministic ruling-line table-grid detection. No OCR, no
recognition — purely geometric structure derived from the rendered bitmap."""

from dip.tablegrid.grid import GridDetectionError, detect_grid
from dip.tablegrid.models import TableGrid

__all__ = ["GridDetectionError", "detect_grid", "TableGrid"]
