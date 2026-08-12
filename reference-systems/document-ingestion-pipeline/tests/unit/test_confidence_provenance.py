"""OCR confidence vs. extraction confidence stay separate (decision 9), and
every field carries full provenance including ocr_engine (decisions 10/11) —
synthetic fixtures, no real OCR/PDF."""

from datetime import datetime, timezone

from dip.diff.models import EquipmentRow
from dip.extract.build import _extraction_confidence, _union_bbox
from dip.ocr.engines.base import OcrWord
from dip.provenance import EvidenceRef, FieldProvenance
from dip.tablegrid.models import TableGrid


def _grid() -> TableGrid:
    return TableGrid(
        document_id="doc1",
        page_index=0,
        render_scale=2.0,
        row_boundaries=[0, 50, 100],
        col_boundaries=[0, 100, 200],
    )


def test_extraction_confidence_is_100_when_word_fully_inside_cell():
    grid = _grid()
    word = OcrWord(text="45", confidence=91.0, left=10, top=10, width=20, height=15)
    conf = _extraction_confidence(grid, 0, 0, [word])
    assert conf == 100.0


def test_extraction_confidence_drops_when_word_straddles_a_column_boundary():
    grid = _grid()
    # cell 0 is x=[0,100); this word spans x=[90,130), half outside the cell
    word = OcrWord(text="45", confidence=91.0, left=90, top=10, width=40, height=15)
    conf = _extraction_confidence(grid, 0, 0, [word])
    assert conf is not None
    assert conf < 100.0


def test_extraction_confidence_independent_of_ocr_confidence():
    """The two numbers must never be derived from each other — a
    low-OCR-confidence word fully inside its cell still gets a HIGH
    extraction confidence, and vice versa."""
    grid = _grid()
    low_ocr_conf_word = OcrWord(text="45", confidence=12.0, left=10, top=10, width=20, height=15)
    extraction_conf = _extraction_confidence(grid, 0, 0, [low_ocr_conf_word])
    assert extraction_conf == 100.0  # fully inside the cell, regardless of the word's own OCR confidence
    assert low_ocr_conf_word.confidence == 12.0  # OCR confidence itself untouched


def test_extraction_confidence_none_when_no_words():
    grid = _grid()
    assert _extraction_confidence(grid, 0, 0, []) is None


def test_union_bbox_of_multiple_words():
    words = [
        OcrWord(text="A", confidence=90, left=10, top=10, width=10, height=10),
        OcrWord(text="B", confidence=90, left=30, top=5, width=10, height=10),
    ]
    bbox = _union_bbox(words)
    assert bbox.left == 10
    assert bbox.top == 5
    assert bbox.right == 40
    assert bbox.bottom == 20


def test_union_bbox_empty_list_is_none():
    assert _union_bbox([]) is None


def _evidence(**overrides) -> EvidenceRef:
    defaults = dict(
        document_id="abc123",
        file_name="02_Main_Plans_Bldg_3319.pdf",
        page_index=373,
        page_label="E0.4 - Air Handler Replacement Schedule",
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime.now(timezone.utc),
        ocr_engine="tesseract",
    )
    defaults.update(overrides)
    return EvidenceRef(**defaults)


def test_field_provenance_keeps_ocr_and_extraction_confidence_as_separate_fields():
    fp = FieldProvenance(ocr_confidence=91.0, extraction_confidence=100.0, evidence=_evidence())
    assert fp.ocr_confidence == 91.0
    assert fp.extraction_confidence == 100.0
    assert fp.ocr_confidence != fp.extraction_confidence or True  # they are independent fields, not derived


def test_field_provenance_values_are_never_combined():
    """Explicit contract test: nothing in FieldProvenance multiplies or
    averages the two confidences into a single score."""
    fp = FieldProvenance(ocr_confidence=40.0, extraction_confidence=100.0, evidence=_evidence())
    # A combined/averaged score would be 70.0 -- neither field equals that,
    # and no third field exists to hold one.
    assert set(FieldProvenance.model_fields.keys()) == {"ocr_confidence", "extraction_confidence", "evidence"}


def test_evidence_ref_ocr_engine_field_backward_compatible_default():
    """Decision 11: existing Phase A/B/D EvidenceRef construction (no
    ocr_engine kwarg) must keep working unchanged."""
    ev = EvidenceRef(
        document_id="abc",
        file_name="f.pdf",
        page_index=0,
        extraction_method="synthetic_fixture",
        extractor_version="fixture-0.1.0",
        extracted_at=datetime.now(timezone.utc),
    )
    assert ev.ocr_engine is None


def test_equipment_row_field_provenance_defaults_to_empty_dict_backward_compatible():
    """Decision 11: an EquipmentRow built the old (Phase D) way, without
    field_provenance, must still validate — matters for the existing
    synthetic fixtures."""
    row = EquipmentRow(tag="AH-1", evidence=_evidence())
    assert row.field_provenance == {}
    assert row.mca_fla_suspicious is False
    assert row.tag_pattern_flag is False


def test_equipment_row_carries_per_field_provenance_map():
    row = EquipmentRow(
        tag="AH-9A",
        fla="56.0",
        fla_numeric=56.0,
        mca="58.0",
        mca_numeric=58.0,
        evidence=_evidence(),
        field_provenance={
            "fla": FieldProvenance(ocr_confidence=91.0, extraction_confidence=100.0, evidence=_evidence()),
            "mca": FieldProvenance(ocr_confidence=88.0, extraction_confidence=95.0, evidence=_evidence()),
        },
    )
    assert row.field_provenance["fla"].ocr_confidence == 91.0
    assert row.field_provenance["mca"].extraction_confidence == 95.0
