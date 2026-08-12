"""Deterministic cell assignment — synthetic grid + synthetic OcrWord
fixtures, no OCR engine, no real PDF."""

from dip.extract.assignment import assign_words_to_cells
from dip.ocr.engines.base import OcrWord
from dip.tablegrid.models import TableGrid


def _grid() -> TableGrid:
    # 3 rows x 2 cols, each cell 100x50
    return TableGrid(
        document_id="doc1",
        page_index=0,
        render_scale=2.0,
        row_boundaries=[0, 50, 100, 150],
        col_boundaries=[0, 100, 200],
    )


def test_word_assigned_to_the_cell_its_centroid_falls_in():
    grid = _grid()
    word = OcrWord(text="AH-1", confidence=90, left=10, top=10, width=30, height=15)  # centroid (25,17.5) -> row0,col0
    cells = assign_words_to_cells(grid, [word])
    assert cells == {(0, 0): [word]}


def test_word_in_second_row_second_column():
    grid = _grid()
    word = OcrWord(text="X", confidence=90, left=150, top=70, width=10, height=10)  # centroid (155,75) -> row1,col1
    cells = assign_words_to_cells(grid, [word])
    assert (1, 1) in cells


def test_word_outside_grid_entirely_is_excluded_not_errored():
    grid = _grid()
    word = OcrWord(text="TITLE", confidence=90, left=10, top=-100, width=30, height=15)  # above the grid
    cells = assign_words_to_cells(grid, [word])
    assert cells == {}


def test_multiple_words_in_same_cell_are_grouped():
    grid = _grid()
    w1 = OcrWord(text="AH-1", confidence=90, left=10, top=10, width=20, height=15)
    w2 = OcrWord(text="(spare)", confidence=80, left=40, top=10, width=20, height=15)
    cells = assign_words_to_cells(grid, [w1, w2])
    assert cells[(0, 0)] == [w1, w2]


def test_word_exactly_on_a_boundary_falls_into_the_cell_that_starts_there():
    grid = _grid()
    # centroid exactly at x=100 (the col boundary) -> should land in col 1, not col 0
    word = OcrWord(text="Y", confidence=90, left=95, top=10, width=10, height=10)  # centroid x=100
    cells = assign_words_to_cells(grid, [word])
    assert (0, 1) in cells
