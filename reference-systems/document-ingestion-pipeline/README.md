# Document Ingestion Pipeline (DIP)

Standalone tooling that turns the real DSH-Atascadero PDF corpus into
provenance-preserving, deterministic evidence. **Not a Downstream service,
not a connector, not a new service boundary.** See
`docs/architecture/DSH_Ingestion_Pipeline_Architecture.md` for the full
architecture and `IMPLEMENTATION_STATUS.md` for how this fits the current
build sequence.

**Current scope: Phase A (manifest), Phase B (OCR benchmark), Phase C (real
structured extraction — E0.4 New Unit block vertical slice only), Phase D
(deterministic synthetic revision diff).** Phase E (promotion into the
Reference Engineering System) is explicitly not implemented here — see the
architecture doc for why.

## Why this lives here, not in `apps/` or `packages/`

`apps/*` is Downstream's own service mesh — DIP is not a Downstream service
and never emits an event onto the Downstream event bus. `packages/*` is
Downstream's shared wire-contract layer — DIP has zero dependency on it, by
design, the same way the Reference Engineering System has zero dependency on
it. DIP is a sibling of `reference-engineering-system` under
`reference-systems/`, with its own `pyproject.toml` and its own pytest
config, exactly matching the "fully independent subsystem" precedent RES
already established for itself.

## Setup

```bash
cd reference-systems/document-ingestion-pipeline
python -m venv .venv
.venv/Scripts/pip install -e ".[dev,ocr]"
```

### Tesseract setup (required for the Tesseract half of the Phase B benchmark)

Installed on this development machine via `winget`:

```powershell
winget install --id UB-Mannheim.TesseractOCR --source winget --accept-package-agreements --accept-source-agreements --silent
```

- **Version installed:** `5.4.0.20240606` (the UB-Mannheim Windows
  distribution — the build `pytesseract`'s own documentation points users
  at, chosen for reproducibility over the alternative winget packages
  `Tesseract.Tesseract.Stable` (2014-era, far too old) and
  `tesseract-ocr.tesseract` (5.5.3, a less commonly documented packaging)).
- **Install location:** `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- **PATH:** winget does **not** retroactively update an already-open shell's
  `PATH` — a new terminal session picks up the machine-level PATH change
  automatically. DIP does **not** assume Tesseract is on `PATH` at all: it
  resolves the binary via `dip.config.resolve_tesseract_cmd()`, which checks,
  in order: the `DIP_TESSERACT_CMD` environment variable, `PATH`, then the
  well-known winget install location above. This is deliberate — relying on
  a freshly-installed binary being on `PATH` in the *current* process is
  exactly the kind of fragile assumption that breaks on the next machine.
- **Reproducing this on another machine:**
  ```powershell
  winget install --id UB-Mannheim.TesseractOCR --source winget --accept-package-agreements --accept-source-agreements
  ```
  If `winget` is unavailable, install manually from
  <https://github.com/UB-Mannheim/tesseract/wiki> (the UB-Mannheim Windows
  installer) and either add the install directory to `PATH` or set
  `DIP_TESSERACT_CMD` to the full path of `tesseract.exe`.
- **If Tesseract cannot be installed:** the OCR benchmark harness degrades
  gracefully — `TesseractEngine.is_available()` returns `False`, the
  benchmark records `engine_available: false` for it, and RapidOCR's results
  are still produced. Nothing in Phase A, Phase D, or the benchmark harness
  itself requires Tesseract to be present.

## Commands

```bash
# Phase A — build manifests for every PDF in the raw corpus
python scripts/build_manifest.py

# Phase A — one file only, ignoring any cached manifest
python scripts/build_manifest.py ../../data/reference-projects/dsh-atascadero/raw/02_Main_Plans_Bldg_3319.pdf --force

# Phase B — benchmark Tesseract + RapidOCR against the 3 named pages (E0.4/E0.6/EE5.1)
python scripts/run_ocr_benchmark.py

# Phase B (implementation-order step 1) — render-scale comparison (2.0/4.0/6.0), both engines
python scripts/run_render_scale_experiment.py

# Phase C — extract the E0.4 New Unit block into structured, provenance-rich EquipmentRows
python -c "from pathlib import Path; from dip.extract.build import extract_new_unit_rows; from dip.ocr.engines.tesseract_engine import TesseractEngine; from dip import config; rows = extract_new_unit_rows(config.DSH_RAW_DIR / config.E04_FILE_NAME, config.E04_PAGE_INDEX, config.E04_SHEET_LABEL, TesseractEngine(), scale=config.RENDER_SCALE); print(len(rows), 'rows')"

# Phase D — synthetic revision diff demo
python scripts/run_synthetic_diff_demo.py

# Tests — fast default suite, no dependency on the real 250MB+ corpus
python -m pytest -q

# Tests — golden suite, exercises the real DSH PDFs, self-skips per-file if absent
python -m pytest -q -m golden
```

## Data layout

```
data/reference-projects/dsh-atascadero/
├── raw/                          # immutable source PDFs — never written to by anything in this package
└── derived/                      # DIP's own cache/output — gitignored (repo root .gitignore already excludes data/)
    ├── documents.json            # registry: document_id -> {file_name, page_count, ...}
    ├── page_manifest/<id>.json   # Phase A output, one file per document
    ├── render_cache/<id>/<page>_s<scale>.png   # Phase B/C: one rendered page image, cached per scale
    ├── ocr_benchmark/<run_id>/{results.json,results.md}   # Phase B output
    └── render_scale_experiment/results.json    # Phase C step 1 output
```

## Phase C — E0.4 New Unit block extraction

Deterministic table reconstruction: rendered bitmap -> ruling-line grid
detection (`dip.tablegrid`, classical projection-profile image analysis, no
ML) -> OCR word-box cell assignment -> New Unit block header scoping ->
normalization/validation -> `list[EquipmentRow]` (`dip.diff.models`), each
field carrying full provenance (`dip.provenance.EvidenceRef` +
`FieldProvenance`, with OCR confidence and extraction confidence kept as
two separate numbers, never combined). Tesseract is the primary OCR engine;
RapidOCR is invoked only as a per-cell fallback when a New Unit field cell
comes back empty from Tesseract — never a second whole-page pass by
default. Scope is deliberately narrow: identity (`tag`,
`existing_designation`) plus the New Unit block's six columns
(`fed_from_panel`, `breaker_rating`, `conduit`, `volts`, `fla`, `mca`) only
— Existing Supply Fan / Existing Return Fan / Conductors / Motor
Controller / Motor Disconnect / Notes are explicitly deferred. See
`tests/golden/test_e04_extraction_against_ground_truth.py` for the
real-data accuracy measurement (91.1% exact field match against an 8-row
manually-transcribed ground truth, `tests/fixtures/e04_ground_truth.json`)
and the implementation report for the full investigation.

## What is explicitly NOT here

- No Phase E (promotion into the Reference Engineering System) — no RES
  contact of any kind exists in this package.
- No Equipment/Material/Asset RES entity, no CreateDrawingVersion, no RES
  API calls, no Downstream event, no Kafka, no Neo4j, no commercial
  reasoning — Phase C's output stays inside DIP, on disk, exactly like
  every earlier phase's.
- No new service, no API, no Kafka, no Neo4j, no Redis, no Docker Compose
  entry — this is a CLI/script tool, invoked manually, per the approved
  scope.
