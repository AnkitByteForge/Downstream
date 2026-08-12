#!/usr/bin/env python
"""Phase C, implementation-order step 1: measure Tesseract + RapidOCR at
render scales 2.0 / 4.0 / 6.0 against the 3 benchmark pages, to decide
render scale by measurement, not assumption. Bounded to the same 3 named
pages the Phase B benchmark already used — never the whole corpus.

Usage:
    python scripts/run_render_scale_experiment.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dip import config  # noqa: E402
from dip.manifest.hashing import sha256_of_file  # noqa: E402
from dip.ocr.engines.rapidocr_engine import RapidOcrEngine  # noqa: E402
from dip.ocr.engines.tesseract_engine import TesseractEngine  # noqa: E402
from dip.ocr.render import render_page  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dip.render_scale_experiment")

SCALES = (2.0, 4.0, 6.0)

# Known tokens per page, same as dip.ocr.report.KNOWN_TOKENS, plus MCA/FLA
# labels specifically (the report's original spot-check never included
# them, and the Phase B run notably never found either).
KNOWN_TOKENS = {
    373: ["AH-9C", "MR4", "MR6", "MR7", "MCA", "FLA"],  # E0.4
    375: ["MR1", "MR4", "MR6", "MRDP"],  # E0.6
    43: ["MRDP", "MVDS-1", "MVGPS2"],  # EE5.1
}


def _fragment_stats(words: list[dict]) -> dict:
    confs = [w["confidence"] for w in words if w["confidence"] is not None]
    non_ascii = [w for w in words if any(ord(c) > 127 for c in w["text"])]
    return {
        "word_count": len(words),
        "single_char_count": sum(1 for w in words if len(w["text"]) == 1),
        "tiny_box_count": sum(1 for w in words if w["width"] < 10 or w["height"] < 8),
        "non_ascii_count": len(non_ascii),
        "avg_confidence": (sum(confs) / len(confs)) if confs else None,
        "min_confidence": min(confs) if confs else None,
    }


def main() -> None:
    engines = [TesseractEngine(), RapidOcrEngine()]
    results = []

    for file_name, page_index, page_label in config.BENCHMARK_PAGES:
        pdf_path = config.DSH_RAW_DIR / file_name
        if not pdf_path.exists():
            log.warning("Missing %s, skipping", pdf_path)
            continue
        document_id = sha256_of_file(pdf_path)
        known_tokens = KNOWN_TOKENS.get(page_index, [])

        for scale in SCALES:
            t_render0 = time.perf_counter()
            image = render_page(pdf_path, document_id, page_index, scale=scale)
            render_seconds = time.perf_counter() - t_render0
            log.info("%s scale=%s rendered %s in %.2fs", page_label, scale, image.size, render_seconds)

            for engine in engines:
                if not engine.is_available():
                    log.warning("%s unavailable: %s", engine.name, engine.unavailable_reason())
                    continue
                try:
                    ocr_result = engine.run(image)
                except Exception as exc:  # noqa: BLE001
                    log.exception("%s failed at scale=%s on %s", engine.name, scale, page_label)
                    results.append(
                        {
                            "page_label": page_label,
                            "scale": scale,
                            "engine": engine.name,
                            "render_seconds": render_seconds,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                words = [w.model_dump() for w in ocr_result.words]
                joined = ocr_result.full_text.upper()
                token_hits = {tok: (tok.upper() in joined) for tok in known_tokens}
                stats = _fragment_stats(words)

                entry = {
                    "page_label": page_label,
                    "scale": scale,
                    "engine": engine.name,
                    "render_seconds": round(render_seconds, 2),
                    "ocr_seconds": round(ocr_result.runtime_seconds, 2),
                    "image_size": list(image.size),
                    "known_token_hits": token_hits,
                    "known_token_recovery_rate": (
                        sum(token_hits.values()) / len(token_hits) if token_hits else None
                    ),
                    **stats,
                }
                results.append(entry)
                log.info(
                    "  %-9s runtime=%6.2fs words=%5d tokens=%d/%d nonascii=%d",
                    engine.name,
                    ocr_result.runtime_seconds,
                    stats["word_count"],
                    sum(token_hits.values()),
                    len(token_hits),
                    stats["non_ascii_count"],
                )

    out_dir = config.DSH_DERIVED_DIR / "render_scale_experiment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    log.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
