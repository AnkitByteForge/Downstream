"""Golden test: ties E.0 (persist) and E.1 (VALID-only filter) to the real,
already-known E0.4 extraction output. Excluded from the default run (see
pyproject.toml addopts), same convention as the other golden tests in this
directory. Self-skips if the real corpus file isn't present.

Reuses the same known-AMBIGUOUS real fields already established and
classified by tests/golden/test_e04_extraction_against_ground_truth.py
(Task 7's KNOWN_MISMATCH_CLASSIFICATION) — no new real data is manufactured
here, per the instruction not to introduce additional real construction
data for this milestone.
"""

from __future__ import annotations

import pytest

from dip import config
from dip.extract.build import extract_new_unit_rows
from dip.manifest.hashing import sha256_of_file
from dip.ocr.engines.tesseract_engine import TesseractEngine
from dip.promote.filter import valid_facts_view
from dip.promote.models import StructuredStateSnapshot
from dip.promote.store import load_structured_state, persist_structured_state

pytestmark = pytest.mark.golden

# The same five real, already-investigated-and-classified OCR mismatches as
# tests/golden/test_e04_extraction_against_ground_truth.py's
# KNOWN_MISMATCH_CLASSIFICATION — every one of these is a real field this
# milestone's safety net must keep out of the promotion-eligible view.
KNOWN_AMBIGUOUS_REAL_FIELDS = {
    ("AH-9C", "breaker_rating"),
    ("AH-9C", "mca"),
    ("AH-K1", "mca"),
    ("AH-24CTA", "mca"),
}


@pytest.fixture(autouse=True)
def isolated_structured_state_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "STRUCTURED_STATE_DIR", tmp_path / "structured_state")
    yield


def _extract_real_e04():
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")
    return extract_new_unit_rows(
        pdf_path,
        config.E04_PAGE_INDEX,
        config.E04_SHEET_LABEL,
        TesseractEngine(),
        scale=config.RENDER_SCALE,
    )


def _snapshot_from(rows) -> StructuredStateSnapshot:
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    return StructuredStateSnapshot(
        document_id=sha256_of_file(pdf_path),
        file_name=config.E04_FILE_NAME,
        page_index=config.E04_PAGE_INDEX,
        page_label=config.E04_SHEET_LABEL,
        extractor_version=rows[0].evidence.extractor_version,
        ocr_engine=rows[0].evidence.ocr_engine,
        render_scale=config.RENDER_SCALE,
        extracted_at=rows[0].evidence.extracted_at,
        rows=rows,
    )


def test_real_e04_extraction_persists_and_round_trips_all_59_rows():
    rows = _extract_real_e04()
    snapshot = _snapshot_from(rows)
    persist_structured_state(snapshot)

    loaded = load_structured_state(
        snapshot.document_id, snapshot.page_index, snapshot.extractor_version, snapshot.ocr_engine, snapshot.render_scale
    )
    assert loaded is not None
    assert len(loaded.rows) == 59
    assert [r.tag for r in loaded.rows] == [r.tag for r in rows]


def test_known_ambiguous_real_fields_never_appear_in_the_valid_view():
    """The central safety property, proven against real evidence: every
    field this repo already knows to be OCR-wrong on the real E0.4 page
    (dropped decimals, "/" misread as "1") must be excluded from
    valid_facts_view — not just in a synthetic unit test, but against the
    actual extraction this pipeline actually produces."""
    rows = _extract_real_e04()
    snapshot = _snapshot_from(rows)

    facts = valid_facts_view(snapshot)
    promoted_pairs = {(f.tag, f.field_name) for f in facts}

    leaked = KNOWN_AMBIGUOUS_REAL_FIELDS & promoted_pairs
    assert not leaked, f"Known-AMBIGUOUS real fields leaked into the promotion-eligible view: {leaked}"


def test_valid_view_only_ever_contains_fields_marked_valid_on_the_real_page():
    rows = _extract_real_e04()
    snapshot = _snapshot_from(rows)
    facts = valid_facts_view(snapshot)

    row_by_tag = {r.tag: r for r in rows}
    for fact in facts:
        row = row_by_tag[fact.tag]
        assert row.field_validation.get(fact.field_name) == "VALID", (
            f"{fact.tag}.{fact.field_name} appeared in the valid view but its own "
            f"field_validation is {row.field_validation.get(fact.field_name)!r}"
        )


def test_valid_view_is_non_empty_on_the_real_page():
    """A sanity floor: the vast majority of real E0.4 fields ARE clean
    (91.1% exact match per the reliability milestone) — an empty valid view
    here would indicate the filter itself is broken, not that the page is
    unusually bad."""
    rows = _extract_real_e04()
    snapshot = _snapshot_from(rows)
    facts = valid_facts_view(snapshot)
    assert len(facts) > 0
