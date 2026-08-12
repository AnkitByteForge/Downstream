"""E.1 — the VALID-only filtering view. Synthetic EquipmentRow data
constructed directly here, covering every ValidationStatus explicitly, so
the exact eligibility rule is proven deterministically without depending
on any particular real OCR outcome."""

from __future__ import annotations

from datetime import datetime, timezone

from dip.diff.models import EquipmentRow
from dip.promote.filter import valid_fields_for_row, valid_facts_view
from dip.promote.models import StructuredStateSnapshot
from dip.provenance import EvidenceRef


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ocr_engine="tesseract",
    )


def _row_with_every_status() -> EquipmentRow:
    """One row deliberately exercising all four ValidationStatus values
    plus a field left entirely absent from field_validation (tag /
    existing_designation never get a validator run against them at all in
    real Phase C output) — the exact five-way partition E.1 must handle."""
    return EquipmentRow(
        tag="AH-9C",
        existing_designation="(E) AH-3",  # never validated -> must never appear in the view
        fed_from_panel="MR4",  # VALID -> eligible
        breaker_rating="2513",  # AMBIGUOUS -> never eligible
        conduit="-",  # INVALID -> never eligible
        volts=None,  # MISSING -> never eligible
        fla="56.0",  # VALID, has a numeric counterpart
        mca="220",  # AMBIGUOUS (dropped-decimal real failure) -> never eligible
        fla_numeric=56.0,
        mca_numeric=None,
        evidence=_evidence(),
        field_validation={
            "fed_from_panel": "VALID",
            "breaker_rating": "AMBIGUOUS",
            "conduit": "INVALID",
            "volts": "MISSING",
            "fla": "VALID",
            "mca": "AMBIGUOUS",
        },
    )


def test_only_valid_fields_are_returned():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)

    field_names = {f.field_name for f in facts}
    assert field_names == {"fed_from_panel", "fla"}


def test_ambiguous_field_is_never_included():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    assert "breaker_rating" not in {f.field_name for f in facts}
    assert "mca" not in {f.field_name for f in facts}


def test_invalid_field_is_never_included():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    assert "conduit" not in {f.field_name for f in facts}


def test_missing_field_is_never_included():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    assert "volts" not in {f.field_name for f in facts}


def test_field_absent_from_field_validation_is_never_included():
    """existing_designation carries a real value but was never validated at
    all — absence of a verdict must not be treated as an implicit VALID."""
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    assert "existing_designation" not in {f.field_name for f in facts}
    assert "tag" not in {f.field_name for f in facts}


def test_valid_field_raw_value_is_preserved_exactly():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    fed_from_panel_fact = next(f for f in facts if f.field_name == "fed_from_panel")
    assert fed_from_panel_fact.raw_value == "MR4"
    assert fed_from_panel_fact.tag == "AH-9C"


def test_valid_numeric_field_carries_its_normalized_value():
    row = _row_with_every_status()
    facts = valid_fields_for_row(row)
    fla_fact = next(f for f in facts if f.field_name == "fla")
    assert fla_fact.raw_value == "56.0"
    assert fla_fact.normalized_value == 56.0


def test_empty_field_validation_yields_no_facts():
    """A row with no validation signal at all (e.g. a Phase D synthetic
    fixture predating Phase C) must yield zero promotion-eligible fields —
    never treated as implicitly all-valid."""
    row = _row_with_every_status().model_copy(update={"field_validation": {}})
    assert valid_fields_for_row(row) == []


def test_filtering_never_mutates_the_source_row():
    row = _row_with_every_status()
    original_validation = dict(row.field_validation)
    original_breaker = row.breaker_rating

    valid_fields_for_row(row)

    assert row.field_validation == original_validation
    assert row.breaker_rating == original_breaker  # still "2513" — untouched


def test_valid_facts_view_aggregates_across_all_rows_in_a_snapshot():
    row_a = _row_with_every_status()
    row_b = _row_with_every_status().model_copy(update={"tag": "AH-11B"})
    snapshot = StructuredStateSnapshot(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extractor_version="dip-extract-0.1.0",
        ocr_engine="tesseract",
        render_scale=2.0,
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        rows=[row_a, row_b],
    )

    facts = valid_facts_view(snapshot)

    assert len(facts) == 4  # 2 VALID fields x 2 rows
    assert {f.tag for f in facts} == {"AH-9C", "AH-11B"}
    assert all(f.field_name in ("fed_from_panel", "fla") for f in facts)


def test_valid_facts_view_on_empty_snapshot_is_empty():
    snapshot = StructuredStateSnapshot(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extractor_version="dip-extract-0.1.0",
        ocr_engine="tesseract",
        render_scale=2.0,
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        rows=[],
    )
    assert valid_facts_view(snapshot) == []
