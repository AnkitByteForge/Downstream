"""Phase A — manifest: opens a source PDF and records per-page facts (page
count, classification, bookmark labels, provenance) without rendering or
OCR-ing anything. See build.py for the entry point."""

from dip.manifest.models import Document, PageManifestEntry
from dip.manifest.classify import PageStats, classify_page

__all__ = ["Document", "PageManifestEntry", "PageStats", "classify_page"]
