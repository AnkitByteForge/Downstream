"""render_page() against a tiny synthetic PDF — cache behavior, never the
real corpus."""

import pypdfium2 as pdfium
import pytest
from PIL import Image

from dip.ocr.render import render_cache_path, render_page


@pytest.fixture()
def tiny_pdf(tmp_path):
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(100, 150)
    path = tmp_path / "tiny.pdf"
    with open(path, "wb") as f:
        pdf.save(f)
    pdf.close()
    return path


@pytest.fixture(autouse=True)
def isolated_render_cache(tmp_path, monkeypatch):
    from dip import config

    monkeypatch.setattr(config, "RENDER_CACHE_DIR", tmp_path / "render_cache")
    yield


def test_render_page_produces_an_image_and_caches_it(tiny_pdf):
    document_id = "fake_doc_id"
    image = render_page(tiny_pdf, document_id, 0)

    assert isinstance(image, Image.Image)
    cache_path = render_cache_path(document_id, 0)
    assert cache_path.exists()


def test_render_page_reuses_cache_without_reopening_pdf(tiny_pdf, monkeypatch):
    document_id = "fake_doc_id"
    render_page(tiny_pdf, document_id, 0)  # populates cache

    import dip.ocr.render as render_module

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("PdfDocument should not be reopened on a cache hit")

    monkeypatch.setattr(render_module.pdfium, "PdfDocument", _fail_if_called)

    image = render_page(tiny_pdf, document_id, 0)
    assert isinstance(image, Image.Image)


def test_force_rerender_bypasses_cache(tiny_pdf):
    document_id = "fake_doc_id"
    render_page(tiny_pdf, document_id, 0)
    image = render_page(tiny_pdf, document_id, 0, force=True)
    assert isinstance(image, Image.Image)
