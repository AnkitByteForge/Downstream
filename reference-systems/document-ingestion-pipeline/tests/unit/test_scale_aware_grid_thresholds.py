"""Task 1 — scale-aware grid-detection thresholds. Pure function tests, no
image, no PDF: proves the linear-scaling relationship directly, calibrated
against the real E0.4 measurements documented in dip.config (row pitch
~30px at scale 2.0, ~60px at scale 4.0 — exactly 2x, matching the scale
ratio exactly)."""

from dip import config


class TestGridMaxRowPitchPx:
    def test_matches_the_calibrated_reference_value_at_reference_scale(self):
        assert config.grid_max_row_pitch_px(2.0) == 80.0

    def test_doubles_when_scale_doubles(self):
        # Measured directly on the real E0.4 render: row pitch went from
        # ~30px at scale 2.0 to ~60px at scale 4.0, exactly 2x.
        assert config.grid_max_row_pitch_px(4.0) == 160.0

    def test_triples_when_scale_triples(self):
        assert config.grid_max_row_pitch_px(6.0) == 240.0

    def test_scales_linearly_not_just_at_measured_points(self):
        assert config.grid_max_row_pitch_px(1.0) == 40.0
        assert config.grid_max_row_pitch_px(3.0) == 120.0


class TestGridLineMergeGapPx:
    def test_matches_the_calibrated_reference_value_at_reference_scale(self):
        assert config.grid_line_merge_gap_px(2.0) == 3.0

    def test_doubles_when_scale_doubles(self):
        assert config.grid_line_merge_gap_px(4.0) == 6.0

    def test_triples_when_scale_triples(self):
        assert config.grid_line_merge_gap_px(6.0) == 9.0


class TestScaleIndependentThresholdsAreUnchanged:
    """Confirms the two thresholds that measurement showed do NOT need to
    scale (dark-pixel intensity, density fractions) were correctly left
    alone — not swept up into the scale-aware change by mistake."""

    def test_dark_pixel_threshold_is_a_plain_constant(self):
        assert config.GRID_DARK_PIXEL_THRESHOLD == 128
        assert isinstance(config.GRID_DARK_PIXEL_THRESHOLD, int)

    def test_density_floors_are_plain_constants(self):
        assert config.GRID_MIN_ROW_LINE_DENSITY == 0.3
        assert config.GRID_MIN_COLUMN_LINE_DENSITY == 0.85
