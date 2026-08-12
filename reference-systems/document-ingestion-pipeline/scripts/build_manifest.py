#!/usr/bin/env python
"""CLI: build a page manifest for one PDF (or every PDF in raw/ if no path given).

Usage:
    python scripts/build_manifest.py                       # all PDFs in data/reference-projects/dsh-atascadero/raw/
    python scripts/build_manifest.py path/to/file.pdf       # one PDF
    python scripts/build_manifest.py path/to/file.pdf --force   # ignore cache
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dip import config  # noqa: E402
from dip.manifest.build import build_manifest  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dip.build_manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", nargs="?", help="Path to one PDF. Omit to process every PDF under raw/.")
    parser.add_argument("--force", action="store_true", help="Recompute even if a cached manifest exists.")
    args = parser.parse_args()

    if args.pdf_path:
        targets = [Path(args.pdf_path)]
    else:
        if not config.DSH_RAW_DIR.exists():
            log.error("Raw corpus directory not found: %s", config.DSH_RAW_DIR)
            sys.exit(1)
        targets = sorted(config.DSH_RAW_DIR.glob("*.pdf"))
        if not targets:
            log.warning("No PDFs found under %s", config.DSH_RAW_DIR)
            return

    for pdf_path in targets:
        try:
            document, entries = build_manifest(pdf_path, force=args.force)
        except Exception:
            log.exception("Failed to build manifest for %s", pdf_path)
            continue
        needs_ocr_count = sum(1 for e in entries if e.needs_ocr)
        log.info(
            "%s -> document_id=%s pages=%d needs_ocr=%d/%d",
            document.file_name,
            document.document_id[:12],
            document.page_count,
            needs_ocr_count,
            document.page_count,
        )


if __name__ == "__main__":
    main()
