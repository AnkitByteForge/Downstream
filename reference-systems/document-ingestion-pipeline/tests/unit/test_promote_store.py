"""E.0 — persist/load structured_state. Synthetic EquipmentRow data only
(constructed directly here or via the existing synthetic_rev_a fixture) —
never the real DSH corpus, so this file runs identically on any machine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dip.diff.models import EquipmentRow
from dip.promote.models import StructuredStateSnapshot
from dip.promote.store import load_structured_state, persist_structured_state, structured_state_path
from dip.provenance import EvidenceRef


@pytest.fixture(autouse=True)
def isolated_structured_state_dir(tmp_path, monkeypatch):
    """Every test in this file writes/reads under an isolated tmp
    directory, never into the repo's real data/.../derived/ tree — same
    isolation convention as tests/unit/test_build.py and test_render.py."""
    from dip import config

    monkeypatch.setattr(config, "STRUCTURED_STATE_DIR", tmp_path / "structured_state")
    yield


def _row(tag: str, breaker_rating: str = "60/3", breaker_status: str = "VALID") -> EquipmentRow:
    evidence = EvidenceRef(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ocr_engine="tesseract",
    )
    return EquipmentRow(
        tag=tag,
        existing_designation="(E) AH-3",
        fed_from_panel="MR4",
        breaker_rating=breaker_rating,
        conduit="1 in",
        volts="480",
        fla="56.0",
        mca="58.0",
        fla_numeric=56.0,
        mca_numeric=58.0,
        evidence=evidence,
        field_validation={
            "fed_from_panel": "VALID",
            "breaker_rating": breaker_status,
            "conduit": "VALID",
            "volts": "VALID",
            "fla": "VALID",
            "mca": "VALID",
        },
    )


def _snapshot(**overrides) -> StructuredStateSnapshot:
    defaults = dict(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extractor_version="dip-extract-0.1.0",
        ocr_engine="tesseract",
        render_scale=2.0,
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        rows=[_row("AH-9A")],
    )
    defaults.update(overrides)
    return StructuredStateSnapshot(**defaults)


def test_persist_creates_the_expected_path(tmp_path):
    snapshot = _snapshot()
    path = persist_structured_state(snapshot)

    expected = structured_state_path("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    assert path == expected
    assert path.exists()


def test_persist_and_load_round_trip_preserves_every_field():
    snapshot = _snapshot()
    persist_structured_state(snapshot)

    loaded = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    assert loaded is not None
    assert loaded == snapshot


def test_load_returns_none_when_nothing_persisted_yet():
    assert load_structured_state("no_such_doc", 0, "v1", "tesseract", 2.0) is None


def test_persistence_identity_distinguishes_render_scale():
    """Two extraction runs of the same document/page/extractor/engine but
    different render_scale must be kept as two independent snapshots, per
    the reliability milestone's finding that render_scale materially
    changes results — never one clobbering the other."""
    snapshot_scale_2 = _snapshot(render_scale=2.0, rows=[_row("AH-9A")])
    snapshot_scale_4 = _snapshot(render_scale=4.0, rows=[_row("AH-9B")])

    persist_structured_state(snapshot_scale_2)
    persist_structured_state(snapshot_scale_4)

    loaded_2 = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    loaded_4 = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 4.0)

    assert loaded_2 is not None and loaded_4 is not None
    assert loaded_2.rows[0].tag == "AH-9A"
    assert loaded_4.rows[0].tag == "AH-9B"


def test_persistence_identity_distinguishes_ocr_engine():
    snapshot_tesseract = _snapshot(ocr_engine="tesseract", rows=[_row("AH-9A")])
    snapshot_rapidocr = _snapshot(ocr_engine="rapidocr", rows=[_row("AH-9B")])

    persist_structured_state(snapshot_tesseract)
    persist_structured_state(snapshot_rapidocr)

    loaded_tess = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    loaded_rapid = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "rapidocr", 2.0)

    assert loaded_tess.rows[0].tag == "AH-9A"
    assert loaded_rapid.rows[0].tag == "AH-9B"


def test_persistence_identity_distinguishes_extractor_version():
    snapshot_v1 = _snapshot(extractor_version="dip-extract-0.1.0", rows=[_row("AH-9A")])
    snapshot_v2 = _snapshot(extractor_version="dip-extract-0.2.0", rows=[_row("AH-9B")])

    persist_structured_state(snapshot_v1)
    persist_structured_state(snapshot_v2)

    loaded_v1 = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    loaded_v2 = load_structured_state("fake_doc_id", 373, "dip-extract-0.2.0", "tesseract", 2.0)

    assert loaded_v1.rows[0].tag == "AH-9A"
    assert loaded_v2.rows[0].tag == "AH-9B"


def test_persistence_identity_distinguishes_document_and_page():
    snapshot_doc_a = _snapshot(document_id="doc_a", page_index=373, rows=[_row("AH-9A")])
    snapshot_doc_b = _snapshot(document_id="doc_b", page_index=373, rows=[_row("AH-9B")])
    snapshot_page_2 = _snapshot(document_id="doc_a", page_index=999, rows=[_row("AH-9C")])

    persist_structured_state(snapshot_doc_a)
    persist_structured_state(snapshot_doc_b)
    persist_structured_state(snapshot_page_2)

    assert load_structured_state("doc_a", 373, "dip-extract-0.1.0", "tesseract", 2.0).rows[0].tag == "AH-9A"
    assert load_structured_state("doc_b", 373, "dip-extract-0.1.0", "tesseract", 2.0).rows[0].tag == "AH-9B"
    assert load_structured_state("doc_a", 999, "dip-extract-0.1.0", "tesseract", 2.0).rows[0].tag == "AH-9C"


def test_deterministic_serialization_same_snapshot_produces_identical_bytes():
    snapshot = _snapshot()
    path_first = persist_structured_state(snapshot)
    bytes_first = path_first.read_bytes()

    path_second = persist_structured_state(snapshot)
    bytes_second = path_second.read_bytes()

    assert bytes_first == bytes_second


def test_idempotent_persistence_does_not_duplicate_or_accumulate(tmp_path):
    """Persisting the same snapshot twice must not create a second file, a
    growing file, or any accumulation — exactly one file at exactly one
    identity, overwritten, not appended."""
    snapshot = _snapshot()
    persist_structured_state(snapshot)
    persist_structured_state(snapshot)
    persist_structured_state(snapshot)

    from dip import config

    all_files = list((config.STRUCTURED_STATE_DIR / "fake_doc_id").glob("*.json"))
    assert len(all_files) == 1

    loaded = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    assert len(loaded.rows) == 1


def test_raw_and_ambiguous_evidence_survive_round_trip_unchanged():
    """Proves persistence never repairs, normalizes, or drops an AMBIGUOUS
    field's raw text — the exact real observed failure this guards against:
    a real breaker_rating OCR'd as "2513" (AMBIGUOUS) must come back out of
    the store as "2513", not "25/3" and not silently dropped."""
    row = _row("AH-9C", breaker_rating="2513", breaker_status="AMBIGUOUS")
    snapshot = _snapshot(rows=[row])
    persist_structured_state(snapshot)

    loaded = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    loaded_row = loaded.rows[0]

    assert loaded_row.breaker_rating == "2513"
    assert loaded_row.field_validation["breaker_rating"] == "AMBIGUOUS"


def test_every_validation_status_survives_round_trip():
    row = _row("AH-9D")
    row = row.model_copy(
        update={
            "field_validation": {
                "fed_from_panel": "VALID",
                "breaker_rating": "AMBIGUOUS",
                "conduit": "INVALID",
                "volts": "MISSING",
            }
        }
    )
    snapshot = _snapshot(rows=[row])
    persist_structured_state(snapshot)

    loaded = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    assert loaded.rows[0].field_validation == {
        "fed_from_panel": "VALID",
        "breaker_rating": "AMBIGUOUS",
        "conduit": "INVALID",
        "volts": "MISSING",
    }


def test_persist_from_clean_environment_with_no_preexisting_directories(tmp_path, monkeypatch):
    """No structured_state directory (or even its parent) exists yet —
    persist_structured_state must create the full path itself, exactly as
    dip.manifest.build._persist and dip.ocr.render.render_page already do
    for their own derived-data trees."""
    from dip import config

    brand_new_root = tmp_path / "does" / "not" / "exist" / "yet"
    assert not brand_new_root.exists()
    monkeypatch.setattr(config, "STRUCTURED_STATE_DIR", brand_new_root)

    snapshot = _snapshot()
    path = persist_structured_state(snapshot)
    assert path.exists()


def test_field_provenance_and_confidence_survive_round_trip():
    from dip.provenance import FieldProvenance

    evidence = EvidenceRef(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ocr_engine="tesseract",
    )
    row = _row("AH-9A").model_copy(
        update={
            "field_provenance": {
                "breaker_rating": FieldProvenance(ocr_confidence=91.5, extraction_confidence=88.0, evidence=evidence),
            }
        }
    )
    snapshot = _snapshot(rows=[row])
    persist_structured_state(snapshot)

    loaded = load_structured_state("fake_doc_id", 373, "dip-extract-0.1.0", "tesseract", 2.0)
    fp = loaded.rows[0].field_provenance["breaker_rating"]
    assert fp.ocr_confidence == 91.5
    assert fp.extraction_confidence == 88.0
    assert fp.evidence.document_id == "fake_doc_id"
