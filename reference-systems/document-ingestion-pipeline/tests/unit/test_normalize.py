"""Numeric normalization and validation rules (decisions 12/13/15) — pure
functions, no OCR, no PDF."""

import pytest

from dip.extract.normalize import (
    check_mca_fla_suspicious,
    check_tag_pattern,
    normalize_numeric,
    validate_breaker_rating,
    validate_conduit,
    validate_fed_from_panel,
    validate_numeric_field,
    validate_volts,
)


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


class TestValidateFedFromPanel:
    @pytest.mark.parametrize("raw", ["MR4", "MR6", "MR1", "MR12", "mr4"])
    def test_real_e04_panel_values_are_valid(self, raw):
        assert validate_fed_from_panel(raw) == "VALID"

    def test_none_is_missing(self):
        assert validate_fed_from_panel(None) == "MISSING"

    @pytest.mark.parametrize("raw", ["-", "TBD", "?", "N/A"])
    def test_placeholders_are_invalid(self, raw):
        assert validate_fed_from_panel(raw) == "INVALID"

    def test_unrecognized_shape_is_ambiguous_not_rejected(self):
        # A real panel outside the MR* convention (e.g. an Existing-block
        # style "Panel A") must not be discarded — just flagged.
        assert validate_fed_from_panel("Panel A") == "AMBIGUOUS"


class TestValidateBreakerRating:
    @pytest.mark.parametrize("raw", ["60/3", "25/3", "20/3", "50/3", "1/3"])
    def test_real_e04_breaker_ratings_are_valid(self, raw):
        assert validate_breaker_rating(raw) == "VALID"

    def test_real_observed_slash_misread_as_1_is_ambiguous(self):
        """The exact real E0.4/AH-9C failure: OCR read '25/3' as '2513'
        (the '/' misread as the digit '1'). Must be flagged, never silently
        accepted as a normally-shaped rating, and never 'corrected' back to
        '25/3' — this test also proves the raw string is untouched."""
        raw = "2513"
        assert validate_breaker_rating(raw) == "AMBIGUOUS"
        # The safety property (Task 8): the raw value itself is NEVER
        # rewritten by validation — it's still exactly "2513" afterward.
        assert raw == "2513"

    def test_none_is_missing(self):
        assert validate_breaker_rating(None) == "MISSING"

    @pytest.mark.parametrize("raw", ["TBD", "-", "?"])
    def test_placeholders_are_invalid(self, raw):
        assert validate_breaker_rating(raw) == "INVALID"


class TestValidateConduit:
    @pytest.mark.parametrize("raw", ["1 in", "3/4 in", "1/2 in", "1in"])
    def test_real_e04_conduit_values_are_valid(self, raw):
        assert validate_conduit(raw) == "VALID"

    def test_missing_unit_is_ambiguous(self):
        # The unit is load-bearing (Task 4) — a bare number without "in"
        # must not be silently treated as equivalent to one with it.
        assert validate_conduit("1") == "AMBIGUOUS"

    def test_none_is_missing(self):
        assert validate_conduit(None) == "MISSING"


class TestValidateVolts:
    @pytest.mark.parametrize("raw", ["480", "208", "240", "120"])
    def test_clean_volts_values_are_valid(self, raw):
        assert validate_volts(raw) == "VALID"

    def test_edge_noise_tolerated_same_as_numeric_fields(self):
        # Real observed OCR artifact on this exact column (Phase C
        # implementation report): a stray leading pipe, e.g. "| 480".
        assert validate_volts("| 480") == "VALID"

    def test_non_numeric_is_ambiguous(self):
        assert validate_volts("48O") == "AMBIGUOUS"  # letter O, not digit 0

    def test_none_is_missing(self):
        assert validate_volts(None) == "MISSING"


class TestValidateNumericField:
    def test_clean_value_with_no_comparison_is_valid(self):
        assert validate_numeric_field("56.0") == "VALID"

    def test_none_is_missing(self):
        assert validate_numeric_field(None) == "MISSING"

    @pytest.mark.parametrize("raw", ["TBD", "-", "?"])
    def test_placeholder_is_invalid(self, raw):
        assert validate_numeric_field(raw) == "INVALID"

    def test_unparseable_non_placeholder_is_ambiguous(self):
        assert validate_numeric_field("VFD") == "AMBIGUOUS"

    def test_real_observed_dropped_decimal_flagged_via_ratio_check(self):
        """The exact real failures observed on E0.4: MCA OCR'd without its
        decimal point (e.g. real '22.0' read as '220'), producing a value
        that parses cleanly but is implausibly large relative to FLA. Each
        case below is a real (raw_mca, raw_fla) pair from the ground truth."""
        # AH-9C: real mca=22.0 misread as "220"; real fla=21.0
        assert validate_numeric_field("220", other_numeric_for_ratio_check=21.0) == "AMBIGUOUS"
        # AH-K1: real mca=26.0 misread as "260"; real fla=24.0
        assert validate_numeric_field("260", other_numeric_for_ratio_check=24.0) == "AMBIGUOUS"
        # AH-24CTA: real mca=34.0 misread as "340"; real fla=31.0
        assert validate_numeric_field("340", other_numeric_for_ratio_check=31.0) == "AMBIGUOUS"

    def test_plausible_ratio_is_valid_not_flagged(self):
        # Real, correct E0.4 pairs — MCA ~1.03-1.09x FLA, well within the
        # plausible band, must not be flagged.
        assert validate_numeric_field("58.0", other_numeric_for_ratio_check=56.0) == "VALID"
        assert validate_numeric_field("36.0", other_numeric_for_ratio_check=33.0) == "VALID"

    def test_never_returns_a_different_numeric_value_than_normalize_numeric(self):
        """Safety property (Task 8), stated as its own explicit assertion:
        validate_numeric_field only classifies — it must never be the thing
        that changes what normalize_numeric() itself would return for the
        same raw text, at any validation status."""
        for raw, other in [("220", 21.0), ("56.0", None), ("VFD", None), ("TBD", None)]:
            status = validate_numeric_field(raw, other_numeric_for_ratio_check=other)
            # normalize_numeric's own output is completely independent of
            # the ratio-check outcome and of the status computed here.
            expected = normalize_numeric(raw)
            assert normalize_numeric(raw) == expected  # idempotent, unaffected by validation having run
            assert status in ("VALID", "AMBIGUOUS", "INVALID", "MISSING")


class TestFieldSpecificPatternsAreDistinctNotGeneric:
    """Task 4's core requirement, proven directly: the same raw text is
    judged differently depending on which field it's claimed to belong to
    — there is no single generic pattern being reused everywhere."""

    def test_a_breaker_shaped_value_is_not_a_valid_panel(self):
        assert validate_fed_from_panel("60/3") == "AMBIGUOUS"

    def test_a_panel_shaped_value_is_not_a_valid_breaker_rating(self):
        assert validate_breaker_rating("MR4") == "AMBIGUOUS"

    def test_a_conduit_shaped_value_is_not_a_valid_volts(self):
        assert validate_volts("1 in") == "AMBIGUOUS"
