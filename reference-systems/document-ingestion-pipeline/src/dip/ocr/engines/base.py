"""OcrEngine — the contract every OCR backend implements.

Keeps the benchmark replaceable, per the approved plan: adding a third
engine later is one new module implementing this Protocol, never a rework
of the benchmark harness.
"""

from __future__ import annotations

from typing import Protocol

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field


class OcrWord(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    confidence: float | None = Field(default=None, description="0-100 if the engine reports one, else None.")
    left: float
    top: float
    width: float
    height: float
    line_group: str | None = Field(
        default=None,
        description=(
            "Engine-specific line/block grouping hint, if the engine provides one "
            "(Tesseract: 'block_par_line'; RapidOCR: None — it has no equivalent hierarchy). "
            "Captured as a supporting signal for future row-grouping cross-checks (Phase C "
            "decision 8) — engine-agnostic code must never require this field to be present."
        ),
    )


class OcrResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_name: str
    full_text: str
    words: list[OcrWord]
    runtime_seconds: float


class OcrEngine(Protocol):
    name: str

    def is_available(self) -> bool:
        """Never raises. False means: skip this engine in the benchmark and
        record why, rather than crash the whole run."""
        ...

    def unavailable_reason(self) -> str | None:
        """Human-readable reason if is_available() is False, else None."""
        ...

    def run(self, image: Image.Image) -> OcrResult:
        """Only called after is_available() is confirmed True."""
        ...
