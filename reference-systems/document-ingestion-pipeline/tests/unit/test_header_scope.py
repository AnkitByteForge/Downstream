"""Header scoping (New Unit block column location) — synthetic header-word
fixtures, no OCR engine, no real PDF. Real-data validation lives in the
golden test."""

import pytest

from dip.extract.header_scope import HeaderScopeError, locate_new_unit_columns
from dip.ocr.engines.base import OcrWord
from dip.tablegrid.models import TableGrid


def _grid(n_cols: int) -> TableGrid:
    return TableGrid(
        document_id="doc1",
        page_index=0,
        render_scale=2.0,
        row_boundaries=[0, 50, 100],
        col_boundaries=[i * 100 for i in range(n_cols + 1)],
    )


def _word(text: str, col_index: int, cell_width: int = 100) -> OcrWord:
    return OcrWord(text=text, confidence=90, left=col_index * cell_width + 10, top=10, width=20, height=15)


def test_locates_new_unit_columns_from_conduit_and_designation_anchors():
    grid = _grid(n_cols=9)  # columns 0-8 valid; anchors below use 1-8
    header_words = [
        _word("DESIGNATION", 1),  # tag
        _word("DESIGNATION", 2),  # existing_designation
        _word("FLA", 3),
        _word("MCA", 4),
        _word("VOLTS", 5),
        _word("PANEL", 6),
        _word("BREAKER", 7),
        _word("CONDUIT", 8),
    ]
    colmap = locate_new_unit_columns(grid, header_words)
    assert colmap.tag_col == 1
    assert colmap.existing_designation_col == 2
    assert colmap.fla_col == 3
    assert colmap.mca_col == 4
    assert colmap.volts_col == 5
    assert colmap.fed_from_panel_col == 6
    assert colmap.breaker_rating_col == 7
    assert colmap.conduit_col == 8


def test_missing_conduit_anchor_raises_header_scope_error():
    grid = _grid(n_cols=4)
    header_words = [_word("DESIGNATION", 0), _word("DESIGNATION", 1)]
    with pytest.raises(HeaderScopeError, match="CONDUIT"):
        locate_new_unit_columns(grid, header_words)


def test_duplicate_conduit_anchor_raises_header_scope_error():
    grid = _grid(n_cols=6)
    header_words = [
        _word("DESIGNATION", 0),
        _word("DESIGNATION", 1),
        _word("CONDUIT", 3),
        _word("CONDUIT", 5),
    ]
    with pytest.raises(HeaderScopeError, match="CONDUIT"):
        locate_new_unit_columns(grid, header_words)


def test_missing_designation_anchors_raises_header_scope_error():
    grid = _grid(n_cols=9)
    header_words = [_word("CONDUIT", 8)]
    with pytest.raises(HeaderScopeError, match="DESIGNATION"):
        locate_new_unit_columns(grid, header_words)


def test_conduit_too_close_to_left_edge_raises_rather_than_negative_column():
    grid = _grid(n_cols=3)
    header_words = [_word("DESIGNATION", 0), _word("DESIGNATION", 1), _word("CONDUIT", 2)]
    with pytest.raises(HeaderScopeError, match="no room"):
        locate_new_unit_columns(grid, header_words)


def test_multi_word_header_cell_text_is_concatenated():
    grid = _grid(n_cols=9)
    header_words = [
        _word("DESIGNATION", 1),
        _word("DESIGNATION", 2),
        _word("FLA", 3),
        _word("MCA", 4),
        _word("VOLTS", 5),
        _word("PANEL", 6),
        OcrWord(text="CIRCUIT", confidence=90, left=7 * 100 + 5, top=10, width=10, height=15),
        OcrWord(text="BREAKER", confidence=90, left=7 * 100 + 20, top=10, width=10, height=15),
        _word("CONDUIT", 8),
    ]
    colmap = locate_new_unit_columns(grid, header_words)
    assert colmap.breaker_rating_col == 7
