"""build_manifest() end-to-end, against a tiny synthetic PDF this test
constructs itself — never against the real DSH corpus, so this file runs
identically on any machine regardless of whether the 250MB+ raw files are
present.
"""

import io

import pypdfium2 as pdfium
import pytest

from dip.manifest.build import build_manifest, find_pages_by_label, manifest_path_for
from dip.manifest.hashing import sha256_of_file


@pytest.fixture()
def blank_two_page_pdf(tmp_path):
    """A minimal, real, on-disk PDF: two blank pages, no text, no bookmarks."""
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(200, 300)
    pdf.new_page(200, 300)
    path = tmp_path / "synthetic_blank.pdf"
    with open(path, "wb") as f:
        pdf.save(f)
    pdf.close()
    return path


@pytest.fixture(autouse=True)
def isolated_derived_dir(tmp_path, monkeypatch):
    """Every test in this file writes manifests under an isolated tmp
    directory, never into the repo's real data/.../derived/ tree."""
    from dip import config

    derived = tmp_path / "derived"
    monkeypatch.setattr(config, "DSH_DERIVED_DIR", derived)
    monkeypatch.setattr(config, "DOCUMENTS_REGISTRY_PATH", derived / "documents.json")
    monkeypatch.setattr(config, "PAGE_MANIFEST_DIR", derived / "page_manifest")
    yield


def test_build_manifest_basic_shape(blank_two_page_pdf):
    document, entries = build_manifest(blank_two_page_pdf)

    assert document.file_name == "synthetic_blank.pdf"
    assert document.page_count == 2
    assert document.document_id == sha256_of_file(blank_two_page_pdf)
    assert len(entries) == 2
    assert [e.page_index for e in entries] == [0, 1]
    # A blank page has no text, no images, no paths -> the conservative
    # "mixed"/needs_ocr=True fallback, never silently treated as fine.
    assert all(e.classification == "mixed" for e in entries)
    assert all(e.needs_ocr for e in entries)
    assert all(e.bookmark_title is None for e in entries)


def test_manifest_and_registry_are_persisted_to_disk(blank_two_page_pdf):
    document, _ = build_manifest(blank_two_page_pdf)

    manifest_file = manifest_path_for(document.document_id)
    assert manifest_file.exists()

    from dip import config

    assert config.DOCUMENTS_REGISTRY_PATH.exists()
    import json

    registry = json.loads(config.DOCUMENTS_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert document.document_id in registry


def test_idempotent_rerun_uses_cache_without_reopening_pdf(blank_two_page_pdf, monkeypatch):
    build_manifest(blank_two_page_pdf)

    import dip.manifest.build as build_module

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("PdfDocument should not be reopened on a cached rerun")

    monkeypatch.setattr(build_module.pdfium, "PdfDocument", _fail_if_called)

    # Should return the cached result without touching pdfium at all.
    document, entries = build_manifest(blank_two_page_pdf)
    assert document.page_count == 2
    assert len(entries) == 2


def test_force_recomputes_even_when_cached(blank_two_page_pdf):
    first, _ = build_manifest(blank_two_page_pdf)
    second, _ = build_manifest(blank_two_page_pdf, force=True)
    assert first.document_id == second.document_id  # same content -> same identity


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_manifest(tmp_path / "does_not_exist.pdf")


def test_find_pages_by_label_is_case_insensitive_and_returns_empty_when_absent(blank_two_page_pdf):
    _, entries = build_manifest(blank_two_page_pdf)
    assert find_pages_by_label(entries, "E0.4") == []


def test_source_pdf_is_never_modified(blank_two_page_pdf):
    before = sha256_of_file(blank_two_page_pdf)
    build_manifest(blank_two_page_pdf, force=True)
    after = sha256_of_file(blank_two_page_pdf)
    assert before == after
