"""Task 8 — the critical production-safety property, tested explicitly and
prominently, separate from the per-function tests already covering it
incidentally in test_normalize.py:

    An ambiguous OCR value is never silently converted into a
    different engineering value.

Exercised at two levels: the pure validator functions (dip.extract.normalize)
and the full EquipmentRow construction path (dip.diff.models), using the
exact real values observed on the real E0.4 sheet during the Phase C
reliability investigation — no synthetic stand-ins for this specific
property, since the property exists to guard against a failure that was
actually observed."""

from datetime import datetime, timezone

from dip.diff.models import EquipmentRow
from dip.extract.normalize import normalize_numeric, validate_breaker_rating, validate_numeric_field
from dip.provenance import EvidenceRef

# The exact real, observed E0.4 mismatches (see IMPLEMENTATION_STATUS.md
# §18.4 / the golden test) — a raw OCR string, what it naively parses/
# passes through as, and the fact that this is NOT the true engineering
# value (kept here only as documentation of why this raw string is a
# meaningful case, never compared against in an assertion — this test
# does not know or assert what the "correct" value would have been).
REAL_OBSERVED_AMBIGUOUS_CASES = [
    ("breaker_rating", "2513"),  # real sheet value is "25/3"; OCR misread "/" as "1"
    ("mca", "220"),  # real sheet value is "22.0"; OCR dropped the decimal point
    ("mca", "260"),  # real sheet value is "26.0"
    ("mca", "340"),  # real sheet value is "34.0"
]


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        document_id="abc123",
        file_name="02_Main_Plans_Bldg_3319.pdf",
        page_index=373,
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime.now(timezone.utc),
        ocr_engine="tesseract",
    )


class TestValidatorsNeverRewriteTheValueTheyClassify:
    def test_breaker_rating_ambiguous_value_is_returned_unmodified_by_caller(self):
        raw = "2513"
        status = validate_breaker_rating(raw)
        assert status == "AMBIGUOUS"
        # The validator returns only a status — it has no return channel
        # for a "corrected" string at all. The caller's own raw variable,
        # unmodified, is what still gets stored on EquipmentRow.
        assert raw == "2513"

    def test_mca_ambiguous_value_normalizes_to_its_own_literal_number_never_a_guessed_one(self):
        # (raw mca, paired real fla) — the exact real E0.4 pairs.
        real_pairs = [("220", 21.0), ("260", 24.0), ("340", 31.0)]
        for raw_mca, real_fla in real_pairs:
            status = validate_numeric_field(raw_mca, other_numeric_for_ratio_check=real_fla)
            assert status == "AMBIGUOUS"
            # normalize_numeric() parses EXACTLY the digits present in raw —
            # "220" becomes 220.0, never silently reinterpreted as 22.0
            # just because 22.0 would be the "more plausible" engineering
            # value. This is the literal safety property.
            assert normalize_numeric(raw_mca) == float(raw_mca)


class TestEquipmentRowNeverAltersAFieldBasedOnItsOwnValidationStatus:
    """The integration-level version of the same property: constructing a
    real EquipmentRow with a known-ambiguous raw value must still store
    that exact raw value, unmodified, regardless of what field_validation
    says about it."""

    def test_ambiguous_breaker_rating_is_stored_verbatim(self):
        row = EquipmentRow(
            tag="AH-9C",
            breaker_rating="2513",  # the real, observed OCR misread
            evidence=_evidence(),
            field_validation={"breaker_rating": validate_breaker_rating("2513")},
        )
        assert row.field_validation["breaker_rating"] == "AMBIGUOUS"
        # The critical assertion: the row's own breaker_rating field is
        # still exactly the raw OCR text — not "25/3", not "" , not None.
        assert row.breaker_rating == "2513"

    def test_ambiguous_mca_is_stored_verbatim_and_numeric_is_its_own_literal_value(self):
        raw_mca = "220"
        row = EquipmentRow(
            tag="AH-9C",
            mca=raw_mca,
            mca_numeric=normalize_numeric(raw_mca),
            fla="21.0",
            fla_numeric=21.0,
            evidence=_evidence(),
            field_validation={"mca": validate_numeric_field(raw_mca, other_numeric_for_ratio_check=21.0)},
        )
        assert row.field_validation["mca"] == "AMBIGUOUS"
        assert row.mca == "220"  # raw untouched
        assert row.mca_numeric == 220.0  # the literal parse of "220" — NOT 22.0

    def test_ambiguity_flag_never_causes_a_field_to_become_none(self):
        """A second failure mode this property must also rule out: silently
        discarding an ambiguous value (treating "uncertain" as "absent")
        would itself be a form of unauthorized alteration."""
        row = EquipmentRow(
            tag="AH-9C",
            breaker_rating="2513",
            evidence=_evidence(),
            field_validation={"breaker_rating": "AMBIGUOUS"},
        )
        assert row.breaker_rating is not None
        assert row.breaker_rating == "2513"

    def test_all_four_real_observed_cases_preserve_their_exact_raw_text(self):
        for field, raw in REAL_OBSERVED_AMBIGUOUS_CASES:
            kwargs = {"tag": "AH-TEST", field: raw, "evidence": _evidence()}
            row = EquipmentRow(**kwargs)
            assert getattr(row, field) == raw, f"{field} was altered from its raw OCR value {raw!r}"
