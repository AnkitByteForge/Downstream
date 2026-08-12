"""Orchestrates: rendered page -> OCR -> grid -> header scoping -> cell
assignment -> normalization -> list[EquipmentRow], for the E0.4 New Unit
block v1 vertical slice.

Tesseract is the primary engine (decision 5). RapidOCR is invoked only as a
per-cell fallback, and only for a New Unit field cell that came back empty
from the primary engine — never as a second whole-page pass by default,
per the explicit instruction not to run both engines for every extraction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from dip.extract.assignment import assign_words_to_cells
from dip.extract.header_scope import HeaderScopeError, NewUnitColumnMap, locate_new_unit_columns
from dip.extract import normalize
from dip.extract.normalize import check_mca_fla_suspicious, check_tag_pattern, normalize_numeric
from dip.diff.models import EquipmentRow
from dip.manifest.hashing import sha256_of_file
from dip.ocr.engines.base import OcrEngine, OcrWord
from dip.ocr.render import render_page
from dip.provenance import BoundingBox, EvidenceRef, FieldProvenance
from dip.tablegrid.grid import detect_grid
from dip.tablegrid.models import TableGrid

EXTRACTOR_VERSION = "dip-extract-0.1.0"

_NEW_UNIT_FIELDS = ("fed_from_panel", "breaker_rating", "conduit", "volts", "fla", "mca")


def _cell_text(words: list[OcrWord]) -> str | None:
    text = " ".join(w.text for w in words).strip()
    return text or None


_TAG_EDGE_NOISE_CHARS = " \t\r\n[]{}|"


def _clean_tag_text(words: list[OcrWord]) -> str | None:
    """Real-data runs against E0.4 found Tesseract intermittently
    prepending a single stray punctuation-like character to this column
    (observed both U+FFFD and U+2018 on the *same* cell across different
    OCR passes — not one fixed character, so a whitelist-based edge-strip
    alone isn't robust). Primary extraction: search for the known-valid
    AH-* shape within the cell text and take just that substring — the tag
    digits/letters themselves were correct in every case observed, only an
    adjacent non-content glyph wasn't. Falls back to edge-noise-stripped raw
    text when no such pattern is found (an unusual tag is possible and must
    not be discarded — it will still be surfaced via tag_pattern_flag)."""
    text = _cell_text(words)
    if text is None:
        return None

    match = normalize.TAG_SEARCH_PATTERN.search(text)
    if match:
        return match.group(0)

    cleaned = text.strip(_TAG_EDGE_NOISE_CHARS)
    return cleaned or None


def _cell_ocr_confidence(words: list[OcrWord]) -> float | None:
    confs = [w.confidence for w in words if w.confidence is not None]
    return sum(confs) / len(confs) if confs else None


def _union_bbox(words: list[OcrWord]) -> BoundingBox | None:
    if not words:
        return None
    lefts = [w.left for w in words]
    tops = [w.top for w in words]
    rights = [w.left + w.width for w in words]
    bottoms = [w.top + w.height for w in words]
    return BoundingBox(left=min(lefts), top=min(tops), right=max(rights), bottom=max(bottoms))


def _extraction_confidence(grid: TableGrid, row: int, col: int, words: list[OcrWord]) -> float | None:
    """How well each word's own box actually fits inside its assigned
    cell's boundaries — a word straddling a column boundary scores lower,
    independent of how confidently the OCR engine read its text."""
    if not words:
        return None
    left, top, right, bottom = grid.cell_bounds(row, col)
    scores = []
    for w in words:
        w_right, w_bottom = w.left + w.width, w.top + w.height
        ox = max(0.0, min(w_right, right) - max(w.left, left))
        oy = max(0.0, min(w_bottom, bottom) - max(w.top, top))
        word_area = max(w.width * w.height, 1e-6)
        scores.append(min(100.0, (ox * oy / word_area) * 100.0))
    return sum(scores) / len(scores)


def _fallback_crop(image: Image.Image, grid: TableGrid, row: int, col: int, margin: int = 4) -> Image.Image:
    left, top, right, bottom = grid.cell_bounds(row, col)
    box = (
        max(0, int(left) - margin),
        max(0, int(top) - margin),
        min(image.width, int(right) + margin),
        min(image.height, int(bottom) + margin),
    )
    return image.crop(box)


def extract_new_unit_rows(
    pdf_path: Path,
    page_index: int,
    page_label: str,
    primary_engine: OcrEngine,
    scale: float,
    fallback_engine: OcrEngine | None = None,
) -> list[EquipmentRow]:
    """Extracts EquipmentRow records for every row whose tag cell has text,
    from the New Unit block only, using the primary engine's whole-page OCR
    pass plus an optional per-cell fallback for New Unit field cells that
    come back empty.

    Raises GridDetectionError / HeaderScopeError rather than returning a
    partial/guessed result if the table structure can't be located at all —
    this function never fabricates row data.
    """
    document_id = sha256_of_file(pdf_path)
    image = render_page(pdf_path, document_id, page_index, scale=scale)
    grid = detect_grid(image, document_id, page_index, scale)

    ocr_result = primary_engine.run(image)
    header_words = [w for w in ocr_result.words if (w.top + w.height / 2.0) < grid.row_boundaries[0]]
    data_words = [w for w in ocr_result.words if (w.top + w.height / 2.0) >= grid.row_boundaries[0]]

    colmap = locate_new_unit_columns(grid, header_words)
    cells = assign_words_to_cells(grid, data_words)

    now = datetime.now(timezone.utc)
    rows: list[EquipmentRow] = []

    for row_idx in range(grid.n_rows):
        tag_words = cells.get((row_idx, colmap.tag_col), [])
        tag_text = _clean_tag_text(tag_words)
        if not tag_text:
            continue  # no equipment tag in this row -> not a data row (e.g. a spacer/notes row)

        field_cells = {
            "fed_from_panel": cells.get((row_idx, colmap.fed_from_panel_col), []),
            "breaker_rating": cells.get((row_idx, colmap.breaker_rating_col), []),
            "conduit": cells.get((row_idx, colmap.conduit_col), []),
            "volts": cells.get((row_idx, colmap.volts_col), []),
            "fla": cells.get((row_idx, colmap.fla_col), []),
            "mca": cells.get((row_idx, colmap.mca_col), []),
        }
        field_cols = {
            "fed_from_panel": colmap.fed_from_panel_col,
            "breaker_rating": colmap.breaker_rating_col,
            "conduit": colmap.conduit_col,
            "volts": colmap.volts_col,
            "fla": colmap.fla_col,
            "mca": colmap.mca_col,
        }
        field_engines = {name: primary_engine.name for name in _NEW_UNIT_FIELDS}

        if fallback_engine is not None:
            for name in _NEW_UNIT_FIELDS:
                if field_cells[name]:
                    continue
                crop = _fallback_crop(image, grid, row_idx, field_cols[name])
                fallback_result = fallback_engine.run(crop)
                if fallback_result.words:
                    left, top, _, _ = grid.cell_bounds(row_idx, field_cols[name])
                    field_cells[name] = [
                        OcrWord(
                            text=w.text,
                            confidence=w.confidence,
                            left=w.left + left - 4,
                            top=w.top + top - 4,
                            width=w.width,
                            height=w.height,
                        )
                        for w in fallback_result.words
                    ]
                    field_engines[name] = fallback_engine.name

        fla_raw = _cell_text(field_cells["fla"])
        mca_raw = _cell_text(field_cells["mca"])
        fla_numeric = normalize_numeric(fla_raw)
        mca_numeric = normalize_numeric(mca_raw)

        row_bbox = _union_bbox(tag_words)
        row_evidence = EvidenceRef(
            document_id=document_id,
            file_name=pdf_path.name,
            page_index=page_index,
            page_label=page_label,
            bounding_box=row_bbox,
            extraction_method="raster_ocr",
            extractor_version=EXTRACTOR_VERSION,
            extracted_at=now,
            ocr_engine=primary_engine.name,
        )

        field_provenance: dict[str, FieldProvenance] = {}
        for name in _NEW_UNIT_FIELDS:
            words = field_cells[name]
            if not words:
                continue
            field_provenance[name] = FieldProvenance(
                ocr_confidence=_cell_ocr_confidence(words),
                extraction_confidence=_extraction_confidence(grid, row_idx, field_cols[name], words),
                evidence=EvidenceRef(
                    document_id=document_id,
                    file_name=pdf_path.name,
                    page_index=page_index,
                    page_label=page_label,
                    bounding_box=_union_bbox(words),
                    extraction_method="raster_ocr",
                    extractor_version=EXTRACTOR_VERSION,
                    extracted_at=now,
                    ocr_engine=field_engines[name],
                ),
            )

        rows.append(
            EquipmentRow(
                tag=tag_text,
                existing_designation=_cell_text(cells.get((row_idx, colmap.existing_designation_col), [])),
                fed_from_panel=_cell_text(field_cells["fed_from_panel"]),
                breaker_rating=_cell_text(field_cells["breaker_rating"]),
                conduit=_cell_text(field_cells["conduit"]),
                volts=_cell_text(field_cells["volts"]),
                fla=fla_raw,
                mca=mca_raw,
                fla_numeric=fla_numeric,
                mca_numeric=mca_numeric,
                mca_fla_suspicious=check_mca_fla_suspicious(mca_numeric, fla_numeric),
                tag_pattern_flag=check_tag_pattern(tag_text),
                evidence=row_evidence,
                field_provenance=field_provenance,
            )
        )

    return rows
