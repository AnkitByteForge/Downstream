"""Numeric normalization and validation rules (decisions 12/13/15) — pure
functions, no OCR, no PDF."""

import pytest

from dip.extract.normalize import check_mca_fla_suspicious, check_tag_pattern, normalize_numeric


class TestNormalizeNumeric:
    def test_clean_integer(self):
        assert normalize_numeric("45") == 45.0

    def test_clean_decimal(self):
        assert normalize_numeric("56.0") == 56.0

    def test_none_input_is_none(self):
        assert normalize_numeric(None) is None

    def test_empty_string_is_none(self):
        assert normalize_numeric("") is None
        assert normalize_numeric("   ") is None

    def test_placeholder_tokens_are_none_never_zero(self):
        for placeholder in ("-", "?", "TBD", "N/A"):
            assert normalize_numeric(placeholder) is None

    def test_edge_noise_is_stripped_real_ocr_pattern(self):
        # Measured directly against real E0.4 OCR output during
        # implementation: pytesseract occasionally appends a stray bracket/
        # pipe adjacent to a ruling-line-crossing cell.
        assert normalize_numeric("56.0|") == 56.0
        assert normalize_numeric("27.0[") == 27.0
        assert normalize_numeric("| 58.0") == 58.0
        assert normalize_numeric("18.0]") == 18.0

    def test_internal_garbage_is_never_force_parsed(self):
        """The edge-noise tolerance must not extend to the middle of the
        string — that would be exactly the 'silently coerce' decision 12
        forbids."""
        assert normalize_numeric("5]8.0") is None
        assert normalize_numeric("2X.0") is None

    def test_non_numeric_text_is_none(self):
        assert normalize_numeric("VFD") is None

    def test_never_fabricates_a_value_from_nothing(self):
        assert normalize_numeric("[]") is None


class TestCheckMcaFlaSuspicious:
    def test_normal_case_mca_greater_than_fla_not_suspicious(self):
        assert check_mca_fla_suspicious(mca_numeric=58.0, fla_numeric=56.0) is False

    def test_mca_less_than_fla_is_suspicious(self):
        assert check_mca_fla_suspicious(mca_numeric=20.0, fla_numeric=45.0) is True

    def test_mca_equal_fla_is_suspicious(self):
        assert check_mca_fla_suspicious(mca_numeric=45.0, fla_numeric=45.0) is True

    def test_missing_mca_is_not_suspicious_nothing_to_compare(self):
        assert check_mca_fla_suspicious(mca_numeric=None, fla_numeric=45.0) is False

    def test_missing_fla_is_not_suspicious(self):
        assert check_mca_fla_suspicious(mca_numeric=58.0, fla_numeric=None) is False

    def test_both_missing_is_not_suspicious(self):
        assert check_mca_fla_suspicious(mca_numeric=None, fla_numeric=None) is False

    def test_never_corrects_only_flags(self):
        """Documents the contract explicitly: this function returns a bool,
        never a corrected value — decision 13."""
        result = check_mca_fla_suspicious(mca_numeric=20.0, fla_numeric=45.0)
        assert isinstance(result, bool)


class TestCheckTagPattern:
    @pytest.mark.parametrize("tag", ["AH-9C", "AH-24CTA", "AH-UP", "AH-CAN", "AH-K1", "AH-MH1", "ah-9c"])
    def test_matching_tags_are_not_flagged(self, tag):
        assert check_tag_pattern(tag) is False

    @pytest.mark.parametrize("tag", ["9C", "FAN-9C", "AHU9C", "RTU-1"])
    def test_non_matching_tags_are_flagged_advisory_only(self, tag):
        assert check_tag_pattern(tag) is True
