"""Golden-file regression test against the real DSH-Atascadero corpus.

Excluded from the default `pytest` run (see pyproject.toml `addopts`).
Run explicitly with: pytest -m golden

Self-skips (rather than failing) if the real PDFs aren't present on this
machine — the default fast suite must never depend on them, and this test
must never be the thing that makes `pytest` fail on a machine that simply
hasn't fetched the 250MB+ corpus.

Every assertion below is a fact independently verified twice: once by the
human-inspection pass in docs/research/DSH_Atascadero_Reconnaissance.md, and
once by directly running dip.manifest.build against the real files during
this Phase A implementation (see the implementation report).
"""

import pytest

from dip import config
from dip.manifest.build import build_manifest, find_pages_by_label

pytestmark = pytest.mark.golden

DOC01 = config.DSH_RAW_DIR / "01_Project_Manual_Book_II.pdf"
DOC02 = config.DSH_RAW_DIR / "02_Main_Plans_Bldg_3319.pdf"
DOC03 = config.DSH_RAW_DIR / "03_Electrical_Plans_Bldg_4872.pdf"
DOC04 = config.DSH_RAW_DIR / "04_Addendum_1.pdf"


def _skip_if_missing(*paths):
    for p in paths:
        if not p.exists():
            pytest.skip(f"DSH corpus file not present: {p}")


def test_doc02_page_count_and_e04_bookmark():
    _skip_if_missing(DOC02)
    document, entries = build_manifest(DOC02)

    assert document.page_count == 425

    e04_pages = find_pages_by_label(entries, "E0.4")
    assert len(e04_pages) >= 1
    e04 = e04_pages[0]
    assert e04.page_index == 373
    assert "AIR HANDLER REPLACEMENT SCHEDULE" in e04.bookmark_title.upper()
    # A raster-embedded schedule table, per reconnaissance §2 mode 2 (~36.9%
    # measured there; ~37.5% measured independently here — both well above
    # the classification floor).
    assert e04.classification == "raster_embedded"
    assert e04.image_coverage_pct >= config.CLASSIFY_RASTER_IMAGE_COVERAGE_PCT


def test_doc02_e06_panel_schedule_page():
    _skip_if_missing(DOC02)
    _, entries = build_manifest(DOC02)

    e06_pages = find_pages_by_label(entries, "E0.6")
    assert len(e06_pages) >= 1
    e06 = e06_pages[0]
    assert e06.page_index == 375
    assert e06.classification == "raster_embedded"


def test_doc03_page_count_and_ee51_vector_curve_bookmark():
    _skip_if_missing(DOC03)
    document, entries = build_manifest(DOC03)

    assert document.page_count == 55

    ee51_pages = find_pages_by_label(entries, "EE5.1")
    assert len(ee51_pages) >= 1
    ee51 = ee51_pages[0]
    assert ee51.page_index == 43
    # Text-drawn-as-vector-curves, per reconnaissance §2 mode 3: near-zero
    # native text, huge PATH object count.
    assert ee51.classification == "vector_curve"
    assert ee51.path_object_count >= config.CLASSIFY_VECTOR_CURVE_PATH_OBJECT_COUNT
    assert ee51.char_len < config.CLASSIFY_VECTOR_CURVE_MAX_TEXT_CHARS


def test_doc04_addendum_page_count_and_first_bookmark():
    _skip_if_missing(DOC04)
    document, entries = build_manifest(DOC04)

    assert document.page_count == 37
    assert entries[0].bookmark_title is not None
    assert "ADDENDUM" in entries[0].bookmark_title.upper()


def test_doc01_spec_book_page_count():
    _skip_if_missing(DOC01)
    document, _entries = build_manifest(DOC01)

    assert document.page_count == 764


def test_source_pdfs_are_never_modified():
    """The single most important invariant: build_manifest must not alter
    the raw corpus in any way. Verified by content hash before/after."""
    _skip_if_missing(DOC02)

    from dip.manifest.hashing import sha256_of_file

    before = sha256_of_file(DOC02)
    build_manifest(DOC02, force=True)
    after = sha256_of_file(DOC02)

    assert before == after
