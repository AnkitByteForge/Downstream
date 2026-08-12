"""Phase B benchmark harness.

Orchestration only — no OCR logic of its own. For each available engine ×
each page in dip.config.BENCHMARK_PAGES, renders once (cached), runs the
engine, and records a BenchmarkEntry. An unavailable engine is recorded, not
fatal — the run always completes with whatever engines are actually usable
on this machine.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from dip import config
from dip.manifest.hashing import sha256_of_file
from dip.ocr.engines.base import OcrEngine, OcrResult
from dip.ocr.render import render_page

log = logging.getLogger(__name__)


class BenchmarkEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_name: str
    engine_available: bool
    unavailable_reason: str | None = None
    document_file_name: str
    document_id: str | None = None
    page_index: int
    page_label: str
    result: OcrResult | None = None
    error: str | None = None


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    started_at: datetime
    entries: list[BenchmarkEntry]


def run_benchmark(engines: list[OcrEngine], raw_dir: Path | None = None) -> BenchmarkRun:
    raw_dir = raw_dir or config.DSH_RAW_DIR
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")

    entries: list[BenchmarkEntry] = []

    for file_name, page_index, page_label in config.BENCHMARK_PAGES:
        pdf_path = raw_dir / file_name
        if not pdf_path.exists():
            for engine in engines:
                entries.append(
                    BenchmarkEntry(
                        engine_name=engine.name,
                        engine_available=engine.is_available(),
                        unavailable_reason=engine.unavailable_reason(),
                        document_file_name=file_name,
                        document_id=None,
                        page_index=page_index,
                        page_label=page_label,
                        error=f"Source PDF not found: {pdf_path}",
                    )
                )
            continue

        document_id = sha256_of_file(pdf_path)
        image = render_page(pdf_path, document_id, page_index)

        for engine in engines:
            available = engine.is_available()
            reason = engine.unavailable_reason()
            if not available:
                log.info("Skipping %s on %s p.%d: %s", engine.name, file_name, page_index, reason)
                entries.append(
                    BenchmarkEntry(
                        engine_name=engine.name,
                        engine_available=False,
                        unavailable_reason=reason,
                        document_file_name=file_name,
                        document_id=document_id,
                        page_index=page_index,
                        page_label=page_label,
                    )
                )
                continue

            try:
                result = engine.run(image)
                entries.append(
                    BenchmarkEntry(
                        engine_name=engine.name,
                        engine_available=True,
                        document_file_name=file_name,
                        document_id=document_id,
                        page_index=page_index,
                        page_label=page_label,
                        result=result,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - one engine's failure must not abort the run
                log.exception("Engine %s failed on %s p.%d", engine.name, file_name, page_index)
                entries.append(
                    BenchmarkEntry(
                        engine_name=engine.name,
                        engine_available=True,
                        document_file_name=file_name,
                        document_id=document_id,
                        page_index=page_index,
                        page_label=page_label,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

    return BenchmarkRun(run_id=run_id, started_at=started_at, entries=entries)


def persist(run: BenchmarkRun) -> Path:
    out_dir = config.OCR_BENCHMARK_DIR / run.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps(run.model_dump(mode="json"), indent=2), encoding="utf-8"
    )
    return out_dir
