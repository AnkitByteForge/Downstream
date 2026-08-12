"""Render exactly one page to an image, cached to disk.

Deliberately narrow: this module never iterates a whole document. Phase B's
benchmark harness calls it once per (document, page) in dip.config.BENCHMARK_PAGES
— rendering is the expensive step the whole "never OCR/render the entire
corpus" constraint exists to bound.
"""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

from dip import config


def render_cache_path(document_id: str, page_index: int, scale: float = config.RENDER_SCALE) -> Path:
    """Cache key includes scale — added for the Phase C render-scale
    experiment. Existing cache entries written before this change (bare
    "<page>.png", implicitly at the old default scale) are simply orphaned,
    not read by this new path convention; the cache is a regenerable
    derived artifact (gitignored), never a system of record, so this is not
    a breaking change to anything persisted."""
    return config.RENDER_CACHE_DIR / document_id / f"{page_index}_s{scale}.png"


def render_page(
    pdf_path: Path,
    document_id: str,
    page_index: int,
    scale: float = config.RENDER_SCALE,
    force: bool = False,
) -> Image.Image:
    """Render one page at the given scale (defaults to dip.config.RENDER_SCALE,
    so every existing caller's signature keeps working unchanged), cached to
    disk keyed by (document_id, page_index, scale). Idempotent: a cached
    render is reused unless force=True."""
    cache_path = render_cache_path(document_id, page_index, scale)
    if cache_path.exists() and not force:
        return Image.open(cache_path).convert("RGB")

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page = pdf.get_page(page_index)
        try:
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil().convert("RGB")
        finally:
            page.close()
    finally:
        pdf.close()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(cache_path)
    return image
