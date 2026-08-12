"""Golden test: run the real Phase C extraction pipeline against the real
E0.4 page and compare against the manually-transcribed ground truth
(tests/fixtures/e04_ground_truth.json — SYNTHETIC: false).

Excluded from the default run (see pyproject.toml addopts), same
convention as tests/golden/test_manifest_against_real_corpus.py. Self-skips
if the real corpus file isn't present.

This test does NOT assert perfect field-level accuracy — the Phase C
investigation and this implementation's own real-data runs found genuine
Tesseract OCR errors (dropped decimal points, "/" misread as "1") on a
handful of fields. Per the Phase C reliability milestone (Task 7), every
mismatch is individually classified (OCR / GRID / CELL_ASSIGNMENT /
NORMALIZATION / GROUND_TRUTH / OTHER) rather than reported as one
aggregate percentage, and the test additionally asserts that every known
mismatch is caught by field_validation (AMBIGUOUS) — proving the Task 3/4
safety net actually flags what it's meant to flag, not just that the raw
text happens to differ from ground truth.
"""

import json
from pathlib import Path

import pytest

from dip import config
from dip.diff.models import EquipmentRow
from dip.extract.build import extract_new_unit_rows
from dip.ocr.engines.tesseract_engine import TesseractEngine
from dip.tablegrid.grid import detect_grid
from dip.ocr.render import render_page
from dip.manifest.hashing import sha256_of_file

pytestmark = pytest.mark.golden

GROUND_TRUTH_PATH = Path(__file__).parent.parent / "fixtures" / "e04_ground_truth.json"
COMPARED_FIELDS = ("existing_designation", "fed_from_panel", "breaker_rating", "conduit", "volts", "fla", "mca")

# Below this exact-match rate, something has genuinely regressed (not just
# the already-known, already-measured OCR errors this test tolerates).
# Measured on the real page during implementation: 51/56 = 91.1% across
# these 8 rows x 7 fields (see the implementation report) — the floor below
# is set with margin under that measurement, not equal to it, so ordinary
# OCR non-determinism doesn't make this test flaky.
MIN_EXACT_MATCH_RATE = 0.80

# Every mismatch this test has ever observed on the real page, with its
# root-cause classification, established by direct investigation (never
# guessed) — see IMPLEMENTATION_STATUS.md §18 for the full trace of each.
# A mismatch NOT in this table is a genuinely new failure and fails the
# test outright, rather than silently passing under the aggregate floor.
KNOWN_MISMATCH_CLASSIFICATION = {
    ("AH-9C", "breaker_rating"): "OCR",  # "/" misread as "1": "25/3" -> "2513"
    ("AH-9C", "mca"): "OCR",  # dropped decimal: "22.0" -> "220"
    ("AH-GSA", "existing_designation"): "OCR",  # dropped space: "(E) GSA UNIT" -> "(E) GSAUNIT"
    ("AH-K1", "mca"): "OCR",  # dropped decimal: "26.0" -> "260"
    ("AH-24CTA", "mca"): "OCR",  # dropped decimal: "34.0" -> "340"
}

# New Unit fields field_validation actually covers (existing_designation
# and tag are validated differently / not at all — see build.py).
VALIDATED_FIELDS = ("fed_from_panel", "breaker_rating", "conduit", "volts", "fla", "mca")


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


def test_e04_new_unit_extraction_field_level_breakdown_against_ground_truth():
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

    total_fields = 0
    matched_fields = 0
    missing_tags: list[str] = []
    row_level: dict[str, dict] = {}  # tag -> {matched, total, mismatches:[...]}
    unclassified_mismatches: list[str] = []

    for expected_row in ground_truth["rows"]:
        tag = expected_row["tag"]
        actual = _find(extracted_rows, tag)
        if actual is None:
            missing_tags.append(tag)
            continue

        row_level[tag] = {"matched": 0, "total": 0, "mismatches": []}

        for field in COMPARED_FIELDS:
            total_fields += 1
            row_level[tag]["total"] += 1
            expected_value = expected_row[field]
            actual_value = (getattr(actual, field) or "").strip(" |[]{}")

            if actual_value == expected_value:
                matched_fields += 1
                row_level[tag]["matched"] += 1
                continue

            classification = KNOWN_MISMATCH_CLASSIFICATION.get((tag, field), "OTHER")
            entry = f"{tag}.{field}: expected {expected_value!r}, got {actual_value!r} [{classification}]"
            row_level[tag]["mismatches"].append(entry)
            if (tag, field) not in KNOWN_MISMATCH_CLASSIFICATION:
                unclassified_mismatches.append(entry)

    # Structural completeness: every ground-truth tag must at least be found
    # as a row (a missing row is a much more serious failure than a wrong
    # field value inside a found row) — Task 2's finding (no rows are
    # actually missing from the table) makes this a meaningful regression
    # guard now, not a known-failing check.
    assert not missing_tags, f"Ground-truth tags not found in extraction output: {missing_tags}"

    # A genuinely NEW mismatch (not one of the 5 already investigated and
    # classified) fails immediately — this is stricter than the aggregate
    # floor below, and is the primary regression signal.
    assert not unclassified_mismatches, (
        "New, unclassified mismatch(es) found — investigate and classify before loosening "
        "KNOWN_MISMATCH_CLASSIFICATION:\n" + "\n".join(unclassified_mismatches)
    )

    match_rate = matched_fields / total_fields if total_fields else 0.0
    assert match_rate >= MIN_EXACT_MATCH_RATE, (
        f"Field match rate {match_rate:.1%} ({matched_fields}/{total_fields}) fell below the "
        f"{MIN_EXACT_MATCH_RATE:.0%} floor."
    )

    # Full breakdown, always printed (not only on failure) — Task 7
    # explicitly asks for row-level and field-level detail, not one number.
    print(f"\n=== Field-level: {matched_fields}/{total_fields} ({match_rate:.1%}) ===")
    for tag, info in row_level.items():
        status = "OK" if not info["mismatches"] else "MISMATCH"
        print(f"  {tag}: {info['matched']}/{info['total']} [{status}]")
        for m in info["mismatches"]:
            print(f"      {m}")
    classification_counts: dict[str, int] = {}
    for (_tag, _field), cls in KNOWN_MISMATCH_CLASSIFICATION.items():
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
    print(f"=== Mismatch classification counts: {classification_counts} ===")
    print("=== GRID: 0, CELL_ASSIGNMENT: 0, NORMALIZATION: 0, GROUND_TRUTH: 0 (no observed failures in these categories) ===")


def test_e04_every_known_mismatch_is_flagged_ambiguous_by_field_validation():
    """Ties Task 3/4's normalization work directly to the real observed
    failures: every field this golden test knows to be wrong on the real
    page must ALSO be flagged AMBIGUOUS by field_validation — proving the
    safety net actually catches what it exists to catch, not just that the
    raw text differs from ground truth."""
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

    unflagged: list[str] = []
    for (tag, field), _classification in KNOWN_MISMATCH_CLASSIFICATION.items():
        if field not in VALIDATED_FIELDS:
            continue  # existing_designation has no dedicated validator (out of Task 4's named field list)
        row = _find(extracted_rows, tag)
        assert row is not None
        status = row.field_validation.get(field)
        if status != "AMBIGUOUS":
            unflagged.append(f"{tag}.{field}: expected AMBIGUOUS, got {status!r}")

    assert not unflagged, "Known-bad fields not caught by field_validation:\n" + "\n".join(unflagged)


def test_e04_row_count_is_stable_and_ah_mh1_is_confirmed_the_last_real_row():
    """Task 2 regression fixture: guards the corrected finding that
    dip.tablegrid detects all 59 real E0.4 New Unit rows, with no missing
    or merged row — AH-MH1 is confirmed (by direct visual inspection of the
    real page) to be the table's true last row, immediately followed by
    prose ("Numbered Notes:"/"General Notes:"), not another equipment row."""
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

    assert len(extracted_rows) == 59, f"Expected 59 real rows, got {len(extracted_rows)}"
    assert extracted_rows[-1].tag == "AH-MH1", (
        f"Expected AH-MH1 (the table's confirmed true last row) to be the final extracted row, "
        f"got {extracted_rows[-1].tag!r}"
    )


def test_grid_detection_is_scale_consistent_at_2_4_and_6(tmp_path):
    """Task 1: grid geometry alone (no OCR) must find the same real
    structure at every tested render scale — 59 rows, 35 columns — proving
    the scale-aware thresholds (dip.config.grid_line_merge_gap_px /
    grid_max_row_pitch_px) generalize, not just happen to work at 2.0."""
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")

    document_id = sha256_of_file(pdf_path)
    results = {}
    for scale in (2.0, 4.0, 6.0):
        image = render_page(pdf_path, document_id, config.E04_PAGE_INDEX, scale=scale)
        grid = detect_grid(image, document_id, config.E04_PAGE_INDEX, scale)
        results[scale] = (grid.n_rows, grid.n_cols)

    print(f"\n=== Grid geometry by scale: {results} ===")
    for scale, (n_rows, n_cols) in results.items():
        assert n_rows == 59, f"scale={scale}: expected 59 rows, got {n_rows}"
        assert n_cols == 35, f"scale={scale}: expected 35 cols, got {n_cols}"


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

    for field in VALIDATED_FIELDS:
        assert field in row.field_provenance, f"missing field_provenance for {field}"
        fp = row.field_provenance[field]
        assert fp.evidence.bounding_box is not None
        assert fp.ocr_confidence is not None
        assert fp.extraction_confidence is not None
        assert row.field_validation.get(field) == "VALID"
