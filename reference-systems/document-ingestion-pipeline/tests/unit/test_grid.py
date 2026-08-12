"""Grid detection against small synthetic images this test draws itself —
never the real corpus. Validates the algorithm's logic, not the specific
thresholds calibrated for the real E0.4 render (those are covered by the
golden test)."""

import pytest
from PIL import Image, ImageDraw

from dip.tablegrid.grid import GridDetectionError, _candidate_boundaries_1d, _longest_regular_band, detect_grid


def _draw_ruled_table(rows: int, cols: int, cell_w: int, cell_h: int) -> Image.Image:
    """A clean synthetic ruled table: solid black lines on white, evenly
    spaced — the simplest case the algorithm must get right."""
    width, height = cols * cell_w + 1, rows * cell_h + 1
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)
    for r in range(rows + 1):
        y = r * cell_h
        draw.line([(0, y), (width, y)], fill=0, width=2)
    for c in range(cols + 1):
        x = c * cell_w
        draw.line([(x, 0), (x, height)], fill=0, width=2)
    return img.convert("RGB")


def test_detects_a_clean_synthetic_ruled_table():
    img = _draw_ruled_table(rows=5, cols=4, cell_w=100, cell_h=60)
    grid = detect_grid(img, "doc1", 0, 2.0)
    assert grid.n_rows == 5
    assert grid.n_cols == 4


def test_raises_when_no_table_present():
    blank = Image.new("RGB", (500, 500), "white")
    with pytest.raises(GridDetectionError):
        detect_grid(blank, "doc1", 0, 2.0)


def test_candidate_boundaries_merges_close_runs():
    import numpy as np

    density = np.zeros(100)
    density[10:13] = 0.9  # one line, 3px wide (anti-aliasing)
    density[50] = 0.9  # another line, 1px
    boundaries = _candidate_boundaries_1d(density, min_density=0.5, merge_gap=3)
    assert len(boundaries) == 2
    assert boundaries[0] == pytest.approx(11.0)
    assert boundaries[1] == pytest.approx(50.0)


def test_candidate_boundaries_empty_when_nothing_exceeds_threshold():
    import numpy as np

    density = np.full(50, 0.1)
    assert _candidate_boundaries_1d(density, min_density=0.5, merge_gap=3) == []


def test_longest_regular_band_picks_the_dense_run_not_sparse_outliers():
    # Simulates the real E0.4 situation: a long regular run, plus sparse,
    # widely-spaced boundaries elsewhere (title-block lines, etc.).
    boundaries = [10, 40, 70, 100, 130, 400, 900]  # first 5 are pitch-30, rest are far outliers
    band = _longest_regular_band(boundaries, max_pitch=50)
    assert band == [10, 40, 70, 100, 130]


def test_longest_regular_band_single_boundary_is_its_own_band():
    assert _longest_regular_band([42.0], max_pitch=50) == [42.0]


def test_longest_regular_band_empty_input():
    assert _longest_regular_band([], max_pitch=50) == []


def test_cell_bounds_returns_expected_rectangle():
    img = _draw_ruled_table(rows=2, cols=2, cell_w=100, cell_h=50)
    grid = detect_grid(img, "doc1", 0, 2.0)
    left, top, right, bottom = grid.cell_bounds(0, 0)
    assert right > left
    assert bottom > top
