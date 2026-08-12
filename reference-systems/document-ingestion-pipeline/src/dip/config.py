"""Named constants for the Document Ingestion Pipeline.

Nothing here is architectural — it is the one place every path and every
heuristic threshold lives, so changing a threshold or a data root never means
hunting through module bodies. Per the approved Phase A/B/D plan, DIP writes
only under a project's own `derived/` tree; the `raw/` tree is read-only.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo layout: this file is at
# reference-systems/document-ingestion-pipeline/src/dip/config.py
REPO_ROOT = Path(__file__).resolve().parents[4]

DSH_PROJECT_ROOT = REPO_ROOT / "data" / "reference-projects" / "dsh-atascadero"
DSH_RAW_DIR = DSH_PROJECT_ROOT / "raw"
DSH_DERIVED_DIR = DSH_PROJECT_ROOT / "derived"

DOCUMENTS_REGISTRY_PATH = DSH_DERIVED_DIR / "documents.json"
PAGE_MANIFEST_DIR = DSH_DERIVED_DIR / "page_manifest"
RENDER_CACHE_DIR = DSH_DERIVED_DIR / "render_cache"
OCR_BENCHMARK_DIR = DSH_DERIVED_DIR / "ocr_benchmark"
DETECTED_CHANGES_DIR = DSH_DERIVED_DIR / "detected_changes"

# --- Phase A: page classification heuristics ---
# Derived directly from the numbers already measured in
# docs/research/DSH_Atascadero_Reconnaissance.md §1-2. These are a starting
# heuristic, not validated ground truth (the reconnaissance report itself
# documents ~73% false positives from a naive text-length-only approach on
# title-block boilerplate) — replaceable via this one module, never inlined.
CLASSIFY_MIN_NATIVE_TEXT_CHARS = 400
CLASSIFY_RASTER_IMAGE_COVERAGE_PCT = 20.0
CLASSIFY_VECTOR_CURVE_PATH_OBJECT_COUNT = 5000
CLASSIFY_VECTOR_CURVE_MAX_TEXT_CHARS = 600

# --- Phase B: OCR benchmark scope ---
# (document filename, 0-indexed page, human label) — exactly the three pages
# the reconnaissance report already inspected and hand-verified content for.
# Never expand this list to "the whole corpus" for benchmarking purposes.
BENCHMARK_PAGES: tuple[tuple[str, int, str], ...] = (
    ("02_Main_Plans_Bldg_3319.pdf", 373, "E0.4 - Air Handler Replacement Schedule"),
    ("02_Main_Plans_Bldg_3319.pdf", 375, "E0.6 - Electrical Panel Schedules"),
    ("03_Electrical_Plans_Bldg_4872.pdf", 43, "EE5.1 - Single Line Diagram"),
)
RENDER_SCALE = 2.0

# Tesseract binary location. PATH is not assumed — see README's
# "Tesseract setup" section for why. Overridable via DIP_TESSERACT_CMD.
TESSERACT_CMD_ENV_VAR = "DIP_TESSERACT_CMD"
TESSERACT_DEFAULT_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def resolve_tesseract_cmd() -> str | None:
    """Return a usable tesseract command path, or None if not found.

    Checks (in order): the env var override, PATH, then the well-known
    winget/UB-Mannheim install locations. Never raises — callers use this to
    decide availability, not to fail fast.
    """
    import shutil

    env_override = os.environ.get(TESSERACT_CMD_ENV_VAR)
    if env_override and Path(env_override).exists():
        return env_override

    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    for candidate in TESSERACT_DEFAULT_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    return None
