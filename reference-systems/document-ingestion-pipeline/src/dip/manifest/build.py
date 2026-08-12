"""Phase A entry point.

Opens a source PDF read-only, walks its pages using page-object/text-layer
inspection only (never rendering, never OCR-ing), and writes a page manifest
JSON plus an entry in the document registry. The source PDF is never
modified — pdfium opens it read-only and no write path exists anywhere in
this module.

Idempotent: document identity is the sha256 of the file's bytes, so
re-running against an unchanged file reproduces the same document_id and,
by default, skips recomputation if a manifest already exists for it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pypdfium2 as pdfium

from dip import config
from dip.manifest.classify import PageStats, classify_page
from dip.manifest.hashing import sha256_of_file
from dip.manifest.models import Document, PageManifestEntry

EXTRACTOR_VERSION = "dip-manifest-0.1.0"


def _bookmark_map(pdf: pdfium.PdfDocument) -> dict[int, str]:
    """page_index -> first outline/bookmark title pointing at that page."""
    mapping: dict[int, str] = {}
    for bookmark in pdf.get_toc():
        dest = bookmark.get_dest()
        if dest is None:
            continue
        page_index = dest.get_index()
        if page_index is None or page_index in mapping:
            continue
        title = bookmark.get_title()
        if title:
            mapping[page_index] = title
    return mapping


def _page_stats(page: pdfium.PdfPage) -> PageStats:
    width, height = page.get_size()
    page_area = max(width * height, 1.0)

    image_area = 0.0
    path_object_count = 0
    for obj in page.get_objects():
        if obj.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE:
            left, bottom, right, top = obj.get_bounds()
            image_area += max(right - left, 0.0) * max(top - bottom, 0.0)
        elif obj.type == pdfium.raw.FPDF_PAGEOBJ_PATH:
            path_object_count += 1

    textpage = page.get_textpage()
    try:
        char_len = textpage.count_chars()
    finally:
        textpage.close()

    image_coverage_pct = min(100.0, (image_area / page_area) * 100.0)
    return PageStats(
        char_len=char_len,
        image_coverage_pct=image_coverage_pct,
        path_object_count=path_object_count,
    )


def manifest_path_for(document_id: str) -> Path:
    return config.PAGE_MANIFEST_DIR / f"{document_id}.json"


def load_manifest(document_id: str) -> list[PageManifestEntry] | None:
    path = manifest_path_for(document_id)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [PageManifestEntry.model_validate(e) for e in raw]


def build_manifest(pdf_path: Path, force: bool = False) -> tuple[Document, list[PageManifestEntry]]:
    """Build (and persist) the page manifest for one PDF.

    If force=False (default) and a manifest already exists for this exact
    file's content hash, the cached manifest is loaded and returned instead
    of re-walking the PDF — cheap reruns, per the quality requirements.
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {pdf_path}")

    document_id = sha256_of_file(pdf_path)

    if not force:
        cached = load_manifest(document_id)
        if cached is not None:
            registry = _load_registry()
            document = Document.model_validate(registry[document_id])
            return document, cached

    now = datetime.now(timezone.utc)

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page_count = len(pdf)
        pdf_version = pdf.get_version()
        bookmarks = _bookmark_map(pdf)

        entries: list[PageManifestEntry] = []
        for page_index in range(page_count):
            page = pdf.get_page(page_index)
            try:
                stats = _page_stats(page)
            finally:
                page.close()

            classification, needs_ocr = classify_page(stats)
            entries.append(
                PageManifestEntry(
                    document_id=document_id,
                    page_index=page_index,
                    char_len=stats.char_len,
                    image_coverage_pct=round(stats.image_coverage_pct, 2),
                    path_object_count=stats.path_object_count,
                    classification=classification,
                    needs_ocr=needs_ocr,
                    bookmark_title=bookmarks.get(page_index),
                    extractor_version=EXTRACTOR_VERSION,
                    extracted_at=now,
                )
            )
    finally:
        pdf.close()

    document = Document(
        document_id=document_id,
        file_name=pdf_path.name,
        page_count=page_count,
        pdf_version=pdf_version,
        file_size_bytes=pdf_path.stat().st_size,
        manifest_built_at=now,
        extractor_version=EXTRACTOR_VERSION,
    )

    _persist(document, entries)
    return document, entries


def _load_registry() -> dict[str, dict]:
    if not config.DOCUMENTS_REGISTRY_PATH.exists():
        return {}
    return json.loads(config.DOCUMENTS_REGISTRY_PATH.read_text(encoding="utf-8"))


def _persist(document: Document, entries: list[PageManifestEntry]) -> None:
    config.PAGE_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path_for(document.document_id).write_text(
        json.dumps([e.model_dump(mode="json") for e in entries], indent=2),
        encoding="utf-8",
    )

    config.DOCUMENTS_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry = _load_registry()
    registry[document.document_id] = document.model_dump(mode="json")
    config.DOCUMENTS_REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def find_pages_by_label(entries: list[PageManifestEntry], label_substring: str) -> list[PageManifestEntry]:
    """Locate manifest entries whose bookmark title contains a substring
    (case-insensitive) — how E0.4/E0.6/EE5.1 are actually located; never a
    hardcoded page-index assumption."""
    needle = label_substring.lower()
    return [e for e in entries if e.bookmark_title and needle in e.bookmark_title.lower()]
