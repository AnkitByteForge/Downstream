"""Golden test: run the real Phase C extraction pipeline against the real
E0.4 page and compare against the manually-transcribed ground truth
(tests/fixtures/e04_ground_truth.json — SYNTHETIC: false).

Excluded from the default run (see pyproject.toml addopts), same
convention as tests/golden/test_manifest_against_real_corpus.py. Self-skips
if the real corpus file isn't present.

This test does NOT assert perfect field-level accuracy — the Phase C
investigation and this implementation's own real-data runs found genuine
Tesseract OCR errors (dropped decimal points, "/" misread as "1") on a
handful of fields. The test measures and asserts a defensible accuracy
floor, and prints every mismatch it finds, so a regression is caught
without pretending an OCR pipeline that admits real errors is perfect.
"""

import json
from pathlib import Path

import pytest

from dip import config
from dip.diff.models import EquipmentRow
from dip.extract.build import extract_new_unit_rows
from dip.ocr.engines.tesseract_engine import TesseractEngine

pytestmark = pytest.mark.golden

GROUND_TRUTH_PATH = Path(__file__).parent.parent / "fixtures" / "e04_ground_truth.json"
COMPARED_FIELDS = ("existing_designation", "fed_from_panel", "breaker_rating", "conduit", "volts", "fla", "mca")

# Below this exact-match rate, something has genuinely regressed (not just
# the already-known, already-measured OCR errors this test tolerates).
# Measured on the real page during implementation: 44/48 = 91.7% across
# these 8 rows x 6 fields (see the implementation report) — the floor below
# is set with margin under that measurement, not equal to it, so ordinary
# OCR non-determinism doesn't make this test flaky.
MIN_EXACT_MATCH_RATE = 0.80


def _load_ground_truth() -> dict:
    payload = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    assert payload["SYNTHETIC"] is False, "e04_ground_truth.json must be marked SYNTHETIC: false"
    assert payload["SOURCE"] == "manual transcription of real E0.4"
    return payload


def _find(rows: list[EquipmentRow], tag: str) -> EquipmentRow | None:
    for r in rows:
        if r.tag == tag:
            return r
    return None


def test_e04_new_unit_extraction_matches_ground_truth_within_measured_tolerance():
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")

    ground_truth = _load_ground_truth()
    extracted_rows = extract_new_unit_rows(
        pdf_path,
        config.E04_PAGE_INDEX,
        config.E04_SHEET_LABEL,
        TesseractEngine(),
        scale=config.RENDER_SCALE,
    )

    mismatches: list[str] = []
    total_fields = 0
    matched_fields = 0
    missing_tags: list[str] = []

    for expected_row in ground_truth["rows"]:
        tag = expected_row["tag"]
        actual = _find(extracted_rows, tag)
        if actual is None:
            missing_tags.append(tag)
            continue

        for field in COMPARED_FIELDS:
            total_fields += 1
            expected_value = expected_row[field]
            actual_value = (getattr(actual, field) or "").strip(" |[]{}")
            if actual_value == expected_value:
                matched_fields += 1
            else:
                mismatches.append(f"{tag}.{field}: expected {expected_value!r}, got {actual_value!r}")

    # Structural completeness: every ground-truth tag must at least be found
    # as a row (a missing row is a much more serious failure than a wrong
    # field value inside a found row).
    assert not missing_tags, f"Ground-truth tags not found in extraction output: {missing_tags}"

    match_rate = matched_fields / total_fields if total_fields else 0.0
    detail = "\n".join(mismatches) if mismatches else "(no mismatches)"
    assert match_rate >= MIN_EXACT_MATCH_RATE, (
        f"Field match rate {match_rate:.1%} ({matched_fields}/{total_fields}) fell below the "
        f"{MIN_EXACT_MATCH_RATE:.0%} floor. Mismatches:\n{detail}"
    )

    # Always visible in -v / -s output, even when the test passes, so known
    # OCR error patterns stay documented rather than silently tolerated.
    print(f"\nField match rate: {match_rate:.1%} ({matched_fields}/{total_fields})")
    if mismatches:
        print("Known mismatches (within tolerance):\n" + detail)


def test_e04_mca_fla_suspicious_flag_never_true_on_ground_truth_rows():
    """Every ground-truth row's real MCA > FLA (true electrical convention) —
    the suspicious flag should never fire on these 8 rows even where OCR
    itself introduces an error (a dropped decimal still produces a *larger*
    MCA reading in every case observed, never one that flips the
    comparison), which would be a correctness regression worth catching
    separately from field-value accuracy."""
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")

    ground_truth = _load_ground_truth()
    extracted_rows = extract_new_unit_rows(
        pdf_path,
        config.E04_PAGE_INDEX,
        config.E04_SHEET_LABEL,
        TesseractEngine(),
        scale=config.RENDER_SCALE,
    )

    for expected_row in ground_truth["rows"]:
        actual = _find(extracted_rows, expected_row["tag"])
        assert actual is not None
        assert actual.mca_fla_suspicious is False, (
            f"{expected_row['tag']}: mca_fla_suspicious=True unexpected "
            f"(mca={actual.mca!r}, fla={actual.fla!r})"
        )


def test_e04_every_extracted_new_unit_field_carries_provenance():
    """Decision 10: every extracted field must be traceable. Spot-checks the
    known-good AH-9A row (no OCR errors observed on it during
    implementation) for full EvidenceRef + FieldProvenance population."""
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")

    extracted_rows = extract_new_unit_rows(
        pdf_path,
        config.E04_PAGE_INDEX,
        config.E04_SHEET_LABEL,
        TesseractEngine(),
        scale=config.RENDER_SCALE,
    )
    row = _find(extracted_rows, "AH-9A")
    assert row is not None

    assert row.evidence.document_id
    assert row.evidence.file_name == config.E04_FILE_NAME
    assert row.evidence.page_index == config.E04_PAGE_INDEX
    assert row.evidence.ocr_engine == "tesseract"
    assert row.evidence.bounding_box is not None

    for field in ("fed_from_panel", "breaker_rating", "conduit", "volts", "fla", "mca"):
        assert field in row.field_provenance, f"missing field_provenance for {field}"
        fp = row.field_provenance[field]
        assert fp.evidence.bounding_box is not None
        assert fp.ocr_confidence is not None
        assert fp.extraction_confidence is not None
