"""Named constants for the Document Ingestion Pipeline.

Nothing here is architectural — it is the one place every path and every
heuristic threshold lives, so changing a threshold or a data root never means
hunting through module bodies. Per the approved Phase A/B/D plan, DIP writes
only under a project's own `derived/` tree; the `raw/` tree is read-only.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

# DIP renders its own pages at scale 6.0 (18144x12960 = ~235M pixels),
# which exceeds Pillow's default MAX_IMAGE_PIXELS (~89.5M, warn) and its
# hard-error threshold (2x that, ~179M) outright — confirmed directly: a
# real DecompressionBombError was raised reloading a scale-6.0 render from
# cache during the Phase C reliability investigation. Raised deliberately
# and only here, to a bounded (not unlimited) ceiling comfortably above
# what this pipeline's own known, fixed render-scale range ever produces —
# this is safe specifically because every image DIP opens is either (a) a
# render this same process just produced from a page count/scale it
# already controls, or (b) that same render reloaded from DIP's own cache;
# never an arbitrary, untrusted, externally-supplied image file.
Image.MAX_IMAGE_PIXELS = 300_000_000

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
# DELIBERATELY LEFT AT 2.0 — an unresolved, flagged contradiction, not a
# silent decision. The Phase C render-scale experiment (2.0/4.0/6.0,
# measured against all 3 benchmark pages, both engines — see the
# implementation report) found 4.0 measurably better for raw OCR quality:
# it matches 6.0's peak Tesseract known-token recovery on E0.4 (5/6, no
# further gain at 6.0) at much lower runtime and noise, and resolves E0.6's
# scale-2.0 runtime pathology (149.6s -> 30.35s) that 6.0 only partially
# fixes. BUT switching the live pipeline's default to 4.0 was tried and
# reverted: it broke dip.tablegrid's row-band detection (59 rows -> 33 —
# GRID_LINE_MERGE_GAP_PX / GRID_MAX_ROW_PITCH_PX were calibrated and
# visually validated only at scale 2.0, and don't transfer cleanly to a
# different pixel density), and reloading a scale-4.0+ render from the
# cache trips PIL's DecompressionBombWarning (104.5MP vs PIL's 89.5MP
# default limit; scale 6.0 renders exceed PIL's hard error threshold
# outright). Recalibrating the grid thresholds for scale 4.0 is real,
# separate follow-up work, not done here — see the implementation report's
# "what remains deferred" section. 2.0 is what dip.tablegrid is actually
# validated against end-to-end.
RENDER_SCALE = 2.0

# --- Phase C: table-grid detection (ruling-line projection profile) ---
# Thresholds calibrated empirically against the real E0.4 render (see the
# Phase C implementation report), not guessed: the render is a crisp,
# born-digital line-art image with a strongly bimodal pixel-value
# histogram (near-0 ink, near-255 background — no scan noise to fight),
# so a fixed binarization threshold is appropriate here (never assumed for
# a scanned source without re-validating this constant). Pixel intensity
# is scale-independent (it's a color threshold, not a size), so this one
# constant does NOT need to scale with render_scale — confirmed by the
# reliability investigation: the same 128 value worked cleanly at every
# scale tested (2.0/4.0/6.0).
GRID_DARK_PIXEL_THRESHOLD = 128

# Row and column line-density floors are FRACTIONS (dark-pixel proportion),
# not pixel counts — dimensionless, and confirmed scale-independent by the
# reliability investigation (the same floors correctly separated genuine
# ruling lines from noise at every scale tested). Measured directly against
# the real E0.4 render: a genuine horizontal ruling line's row-density sits
# around 0.63-0.68 (0.3 cleanly separates it from blank rows). Column
# density is noisier — coincidental vertical alignment of repeated digits/
# text across many rows produces a "candidate" cluster in the 0.3-0.6
# density range, distinct from genuine full-height vertical rules, which
# measured >=0.9 in every case sampled. 0.85 was chosen as the floor
# between these two measured clusters, not an arbitrary guess.
GRID_MIN_ROW_LINE_DENSITY = 0.3
GRID_MIN_COLUMN_LINE_DENSITY = 0.85

# GRID_LINE_MERGE_GAP_PX and GRID_MAX_ROW_PITCH_PX ARE pixel-count
# thresholds, and pixel counts scale linearly with render_scale by
# construction (pdfium renders at `scale x 72 DPI`; doubling scale doubles
# every distance in pixels). This was the genuine, scale-dependent gap the
# reliability investigation was tasked with finding — confirmed by direct
# measurement, not assumed: real row pitch on E0.4 measured ~30px at scale
# 2.0 and ~60px at scale 4.0, exactly 2x, matching the scale ratio exactly.
# Both constants below are therefore defined at a REFERENCE scale and
# scaled linearly by grid_line_merge_gap_px()/grid_max_row_pitch_px() —
# never used as bare module-level constants directly by grid.py.
_GRID_THRESHOLD_REFERENCE_SCALE = 2.0
_GRID_LINE_MERGE_GAP_PX_AT_REFERENCE_SCALE = 3
_GRID_MAX_ROW_PITCH_PX_AT_REFERENCE_SCALE = 80


def grid_line_merge_gap_px(render_scale: float) -> float:
    """Pixel gap below which two candidate ruling-line detections are
    merged into one boundary — scales linearly with render_scale because a
    line's anti-aliased pixel width does too (measured, not assumed)."""
    return _GRID_LINE_MERGE_GAP_PX_AT_REFERENCE_SCALE * (render_scale / _GRID_THRESHOLD_REFERENCE_SCALE)


def grid_max_row_pitch_px(render_scale: float) -> float:
    """Maximum pixel gap between consecutive row boundaries still
    considered part of the same regular table band — scales linearly with
    render_scale because real row height in pixels does too (measured
    directly: ~30px at scale 2.0, ~60px at scale 4.0 on the real E0.4
    render — exactly proportional to the scale ratio)."""
    return _GRID_MAX_ROW_PITCH_PX_AT_REFERENCE_SCALE * (render_scale / _GRID_THRESHOLD_REFERENCE_SCALE)

# --- Phase C: E0.4 vertical-slice identity (v1 scope, per approved decisions) ---
E04_FILE_NAME = "02_Main_Plans_Bldg_3319.pdf"
E04_PAGE_INDEX = 373
E04_SHEET_LABEL = "E0.4 - Air Handler Replacement Schedule"

TABLE_GRID_DIR = DSH_DERIVED_DIR / "table_grid"
EQUIPMENT_ROWS_DIR = DSH_DERIVED_DIR / "equipment_rows"

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
