#!/usr/bin/env python
"""CLI: benchmark Tesseract + RapidOCR against the 3 named DSH pages
(E0.4/E0.6/EE5.1) — never the whole corpus.

Usage:
    python scripts/run_ocr_benchmark.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dip.ocr.benchmark import persist, run_benchmark  # noqa: E402
from dip.ocr.engines.rapidocr_engine import RapidOcrEngine  # noqa: E402
from dip.ocr.engines.tesseract_engine import TesseractEngine  # noqa: E402
from dip.ocr.report import render_markdown  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dip.run_ocr_benchmark")


def main() -> None:
    engines = [TesseractEngine(), RapidOcrEngine()]
    for engine in engines:
        if engine.is_available():
            log.info("%s: available", engine.name)
        else:
            log.warning("%s: unavailable — %s", engine.name, engine.unavailable_reason())

    run = run_benchmark(engines)
    out_dir = persist(run)

    markdown = render_markdown(run)
    (out_dir / "results.md").write_text(markdown, encoding="utf-8")

    log.info("Wrote %s and %s", out_dir / "results.json", out_dir / "results.md")


if __name__ == "__main__":
    main()
