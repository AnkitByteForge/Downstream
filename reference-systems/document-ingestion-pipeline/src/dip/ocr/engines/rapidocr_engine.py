"""RapidOCR engine wrapper — the pure-pip candidate (ONNX Runtime, no system
binary). See the Phase B plan's decision rationale in
docs/architecture/DSH_Ingestion_Pipeline_Architecture.md-adjacent planning:
chosen over easyocr for a lighter install (no PyTorch) and PP-OCR's tuning
toward dense small-font/tabular content, to be *measured*, not assumed, by
this same benchmark.
"""

from __future__ import annotations

import time

import numpy as np
from PIL import Image

from dip.ocr.engines.base import OcrResult, OcrWord

ENGINE_NAME = "rapidocr"


class RapidOcrEngine:
    name = ENGINE_NAME

    def __init__(self) -> None:
        self._engine = None
        self._init_error: str | None = None
        try:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
        except Exception as exc:  # pragma: no cover - environment-dependent
            self._init_error = f"{type(exc).__name__}: {exc}"

    def is_available(self) -> bool:
        return self._engine is not None

    def unavailable_reason(self) -> str | None:
        if self._engine is not None:
            return None
        return self._init_error or "rapidocr_onnxruntime failed to initialize."

    def run(self, image: Image.Image) -> OcrResult:
        assert self._engine is not None

        array = np.array(image)
        t0 = time.perf_counter()
        result, _elapse = self._engine(array)
        runtime = time.perf_counter() - t0

        words: list[OcrWord] = []
        texts: list[str] = []
        for entry in result or []:
            box, text, score = entry[0], entry[1], entry[2]
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            left, top = min(xs), min(ys)
            width, height = max(xs) - left, max(ys) - top
            confidence = float(score) * 100.0 if score is not None else None
            words.append(
                OcrWord(
                    text=text,
                    confidence=confidence,
                    left=float(left),
                    top=float(top),
                    width=float(width),
                    height=float(height),
                )
            )
            texts.append(text)

        return OcrResult(
            engine_name=self.name,
            full_text=" ".join(texts),
            words=words,
            runtime_seconds=runtime,
        )
