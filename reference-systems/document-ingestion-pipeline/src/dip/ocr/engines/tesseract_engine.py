"""Tesseract engine wrapper. Requires the system Tesseract binary — see the
README's "Tesseract setup" section. Never raises on missing binary; reports
unavailable instead, per the benchmark harness's graceful-degradation
requirement.
"""

from __future__ import annotations

import time

from PIL import Image

from dip import config
from dip.ocr.engines.base import OcrResult, OcrWord

ENGINE_NAME = "tesseract"


class TesseractEngine:
    name = ENGINE_NAME

    def __init__(self) -> None:
        self._cmd: str | None = config.resolve_tesseract_cmd()

    def is_available(self) -> bool:
        return self._cmd is not None

    def unavailable_reason(self) -> str | None:
        if self._cmd is not None:
            return None
        return (
            "Tesseract binary not found via DIP_TESSERACT_CMD, PATH, or the "
            "well-known winget install location. See README 'Tesseract setup'."
        )

    def run(self, image: Image.Image) -> OcrResult:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = self._cmd

        t0 = time.perf_counter()
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        runtime = time.perf_counter() - t0

        words: list[OcrWord] = []
        texts: list[str] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            conf_raw = data["conf"][i]
            try:
                conf = float(conf_raw)
            except (TypeError, ValueError):
                conf = None
            if conf is not None and conf < 0:
                conf = None  # tesseract uses -1 for "no confidence" rows
            words.append(
                OcrWord(
                    text=text,
                    confidence=conf,
                    left=float(data["left"][i]),
                    top=float(data["top"][i]),
                    width=float(data["width"][i]),
                    height=float(data["height"][i]),
                )
            )
            texts.append(text)

        return OcrResult(
            engine_name=self.name,
            full_text=" ".join(texts),
            words=words,
            runtime_seconds=runtime,
        )
