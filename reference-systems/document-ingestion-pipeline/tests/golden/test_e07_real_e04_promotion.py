"""E.7 -- the first real end-to-end DIP -> RES Engineering Evidence
Promotion, using the real E0.4 Rev A corpus.

This test runs RES as a genuinely SEPARATE OS process, in RES's own
virtualenv (`reference-systems/reference-engineering-system/backend/.venv`)
-- not an in-process import, not an ASGI in-process transport. DIP's own
test process never imports SQLAlchemy, psycopg, or any RES module; it
only ever speaks HTTP to RES over a real loopback socket, through
dip.promote.res_client's real `requests`-based transport. This is the
strongest available proof of "no direct database write occurs from DIP"
(§ below) and matches the actual production shape: two independent
processes/environments, communicating only over the network.

Self-skips (never fails) if:
  - the real E0.4 PDF isn't present in this checkout, or
  - RES's own .venv isn't present, or
  - RES's Postgres test container isn't reachable (the seed subprocess
    will fail fast and this test skips rather than hard-failing on an
    environment precondition it doesn't own).

Proves the 12 points named in the milestone spec; see the numbered
assertions inside test_e07_real_e04_promotion_end_to_end.

E0.4 has only one real revision in the corpus (Rev A) -- this test
promotes that single real revision as an initial DrawingVersion. It does
NOT promote or claim a real revision *diff*; the synthetic Phase D
Rev A/B fixtures remain the only place a revision diff is exercised, and
remain explicitly marked SYNTHETIC there.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests

from dip import config
from dip.extract.build import extract_new_unit_rows
from dip.manifest.hashing import sha256_of_file
from dip.ocr.engines.tesseract_engine import TesseractEngine
from dip.promote.build import parse_evidence_ref_uri, promote_snapshot
from dip.promote.filter import valid_facts_view
from dip.promote.models import StructuredStateSnapshot
from dip.promote.res_client import ResClientConfig, ResPromotionClient
from dip.promote.store import load_structured_state, persist_structured_state

pytestmark = pytest.mark.golden

_REPO_ROOT = Path(__file__).resolve().parents[4]
_RES_BACKEND_DIR = _REPO_ROOT / "reference-systems" / "reference-engineering-system" / "backend"
_RES_VENV_PYTHON = _RES_BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
_SEED_SCRIPT = _RES_BACKEND_DIR / "scripts" / "seed_dip_promotion_test_client.py"

# The same real, already-investigated-and-classified OCR mismatches as
# tests/golden/test_e04_extraction_against_ground_truth.py's
# KNOWN_MISMATCH_CLASSIFICATION -- reused, not re-derived, per the
# instruction not to manufacture additional real construction data.
KNOWN_AMBIGUOUS_REAL_FIELDS = {
    ("AH-9C", "breaker_rating"),
    ("AH-9C", "mca"),
    ("AH-K1", "mca"),
    ("AH-24CTA", "mca"),
}

TARGET_SHEET_NUMBER = "E0.4"
TARGET_REVISION_LABEL = "Rev A"
TARGET_DISCIPLINE_CODE = "E"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_health(base_url: str, proc: subprocess.Popen, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            pytest.skip(f"RES server process exited early during startup:\n{output}")
        try:
            resp = requests.get(f"{base_url}/health", timeout=1)
            if resp.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.3)
    proc.kill()
    pytest.skip(f"RES server did not become healthy within {timeout}s at {base_url}")


@pytest.fixture(scope="module")
def e07_environment(tmp_path_factory):
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    if not pdf_path.exists():
        pytest.skip(f"DSH corpus file not present: {pdf_path}")
    if not _RES_VENV_PYTHON.exists():
        pytest.skip(f"RES backend .venv not found at {_RES_VENV_PYTHON} -- cannot run the E.7 cross-system test")

    seed = subprocess.run(
        [str(_RES_VENV_PYTHON), str(_SEED_SCRIPT)],
        cwd=_RES_BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if seed.returncode != 0:
        pytest.skip(
            "Could not seed the RES test project (is RES's Postgres test "
            f"container running on port 5433?):\n{seed.stderr}"
        )
    creds = json.loads(seed.stdout.strip().splitlines()[-1])

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [str(_RES_VENV_PYTHON), "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=_RES_BACKEND_DIR / "src",
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_health(base_url, proc)

        derived = tmp_path_factory.mktemp("e07_derived")
        original_structured_state_dir = config.STRUCTURED_STATE_DIR
        original_promotion_log_dir = config.PROMOTION_LOG_DIR
        config.STRUCTURED_STATE_DIR = derived / "structured_state"
        config.PROMOTION_LOG_DIR = derived / "promotion_log"

        yield {"base_url": base_url, **creds}

    finally:
        config.STRUCTURED_STATE_DIR = original_structured_state_dir
        config.PROMOTION_LOG_DIR = original_promotion_log_dir
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def e07_snapshot() -> StructuredStateSnapshot:
    """Real extraction, run exactly once for the whole module (Tesseract
    OCR on the full page is the expensive step) -- point 1/2/3 below."""
    pdf_path = config.DSH_RAW_DIR / config.E04_FILE_NAME
    rows = extract_new_unit_rows(
        pdf_path,
        config.E04_PAGE_INDEX,
        config.E04_SHEET_LABEL,
        TesseractEngine(),
        scale=config.RENDER_SCALE,  # point 2: the established scale-2.0 baseline, not scale-4.0
    )
    assert len(rows) == 59  # confirms E0.4's real table was located correctly (point 1)

    return StructuredStateSnapshot(
        document_id=sha256_of_file(pdf_path),
        file_name=config.E04_FILE_NAME,
        page_index=config.E04_PAGE_INDEX,
        page_label=config.E04_SHEET_LABEL,
        extractor_version=rows[0].evidence.extractor_version,
        ocr_engine=rows[0].evidence.ocr_engine,
        render_scale=config.RENDER_SCALE,
        extracted_at=rows[0].evidence.extracted_at,
        rows=rows,
    )


def test_no_direct_database_write_occurs_from_dip():
    """Point 12, proven structurally by scanning DIP's own source tree: no
    module under dip.promote (or anywhere else in dip/) ever imports a
    database driver or ORM. This is a property of DIP's CODE, checked
    regardless of what happens to be pip-installed in any given dev
    machine's Python environment (both sqlalchemy and psycopg are, in
    fact, importable in this environment for unrelated reasons -- an
    environment-presence check would be a false proof; a source-level
    check of what dip/ actually imports is the real, durable one). The
    only way dip.promote can affect RES's rows is the HTTP calls in
    dip.promote.res_client."""
    dip_src_dir = Path(__file__).resolve().parents[2] / "src" / "dip"
    forbidden_import_markers = ("import psycopg", "import sqlalchemy", "from psycopg", "from sqlalchemy")
    offending: list[str] = []
    for py_file in dip_src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for marker in forbidden_import_markers:
            if marker in text:
                offending.append(f"{py_file.relative_to(dip_src_dir)}: {marker!r}")
    assert not offending, f"dip/ must never import a database driver/ORM directly: {offending}"


def test_e07_real_e04_promotion_end_to_end(e07_environment, e07_snapshot):
    # --- point 3: structured state exists, persisted and reloadable -----
    persist_structured_state(e07_snapshot)
    reloaded = load_structured_state(
        e07_snapshot.document_id,
        e07_snapshot.page_index,
        e07_snapshot.extractor_version,
        e07_snapshot.ocr_engine,
        e07_snapshot.render_scale,
    )
    assert reloaded is not None
    assert len(reloaded.rows) == 59

    # --- points 4/5: only VALID facts are promotion-eligible -------------
    facts = valid_facts_view(reloaded)
    promoted_pairs = {(f.tag, f.field_name) for f in facts}
    leaked = KNOWN_AMBIGUOUS_REAL_FIELDS & promoted_pairs
    assert not leaked, f"Known-AMBIGUOUS real fields leaked into the promotion-eligible view: {leaked}"
    assert len(facts) > 0

    client = ResPromotionClient(
        ResClientConfig(
            base_url=e07_environment["base_url"],
            client_id=e07_environment["client_id"],
            client_secret=e07_environment["client_secret"],
        )
    )

    result_1 = promote_snapshot(
        reloaded,
        client,
        target_project_id=e07_environment["project_id"],
        sheet_number=TARGET_SHEET_NUMBER,
        drawing_title=config.E04_SHEET_LABEL,
        discipline_code=TARGET_DISCIPLINE_CODE,
        revision_label=TARGET_REVISION_LABEL,
    )
    assert result_1.attempt.outcome == "SUCCESS"

    # --- points 6/7: Drawing and DrawingVersion each created exactly once,
    # confirmed by re-querying RES's own list APIs (not just trusting the
    # single POST response) -----------------------------------------------
    session = requests.Session()
    headers = {"Authorization": f"Bearer {client._ensure_token()}"}
    project_id = e07_environment["project_id"]

    drawings = session.get(
        f"{e07_environment['base_url']}/rest/v1.0/projects/{project_id}/documents", headers=headers
    ).json()
    matching_drawings = [d for d in drawings if d["sheet_number"] == TARGET_SHEET_NUMBER]
    assert len(matching_drawings) == 1, f"Expected exactly one E0.4 Drawing, found {len(matching_drawings)}"
    drawing_id = matching_drawings[0]["id"]

    versions = session.get(
        f"{e07_environment['base_url']}/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        headers=headers,
    ).json()
    matching_versions = [v for v in versions if v["revision_label"] == TARGET_REVISION_LABEL]
    assert len(matching_versions) == 1, f"Expected exactly one Rev A DrawingVersion, found {len(matching_versions)}"
    version = matching_versions[0]

    # --- point 8: source_evidence_ref exists on every promoted cloud -----
    assert len(version["revision_clouds"]) == len(facts)
    for cloud in version["revision_clouds"]:
        assert cloud["source_evidence_ref"] is not None

    # --- point 9: the reference resolves conceptually back to DIP's own
    # provenance identity, not just a plausible-looking string -----------
    sample_cloud = version["revision_clouds"][0]
    parsed = parse_evidence_ref_uri(sample_cloud["source_evidence_ref"])
    assert parsed["document_id"] == e07_snapshot.document_id
    assert parsed["page_index"] == e07_snapshot.page_index
    resolved_row = next(r for r in reloaded.rows if r.tag == parsed["tag"])
    assert getattr(resolved_row, str(parsed["field_name"])) is not None

    # --- point 10: rerunning promotion is idempotent ----------------------
    result_2 = promote_snapshot(
        reloaded,
        client,
        target_project_id=project_id,
        sheet_number=TARGET_SHEET_NUMBER,
        drawing_title=config.E04_SHEET_LABEL,
        discipline_code=TARGET_DISCIPLINE_CODE,
        revision_label=TARGET_REVISION_LABEL,
    )
    assert result_2.drawing["id"] == result_1.drawing["id"]
    assert result_2.drawing_version["id"] == result_1.drawing_version["id"]

    drawings_after_rerun = session.get(
        f"{e07_environment['base_url']}/rest/v1.0/projects/{project_id}/documents", headers=headers
    ).json()
    assert len([d for d in drawings_after_rerun if d["sheet_number"] == TARGET_SHEET_NUMBER]) == 1

    versions_after_rerun = session.get(
        f"{e07_environment['base_url']}/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
        headers=headers,
    ).json()
    assert len([v for v in versions_after_rerun if v["revision_label"] == TARGET_REVISION_LABEL]) == 1

    # --- point 11: RES remains the engineering system of record -- the
    # promoted Drawing/DrawingVersion are independently visible through
    # RES's own plain GET API, using a token acquired with a raw HTTP call
    # that never touches dip.promote.res_client at all (not even for
    # authentication) -- genuinely no DIP code in this verification path.
    independent_token_resp = requests.post(
        f"{e07_environment['base_url']}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": e07_environment["client_id"],
            "client_secret": e07_environment["client_secret"],
        },
        timeout=5,
    )
    assert independent_token_resp.status_code == 200
    independent_headers = {"Authorization": f"Bearer {independent_token_resp.json()['access_token']}"}

    independent_check = requests.get(
        f"{e07_environment['base_url']}/rest/v1.0/projects/{project_id}/documents/{drawing_id}",
        headers=independent_headers,
        timeout=5,
    )
    assert independent_check.status_code == 200
    assert independent_check.json()["sheet_number"] == TARGET_SHEET_NUMBER

    # --- explicit non-claim, per instruction: only one real revision
    # exists in the corpus; no real diff was promoted or asserted here ---
    assert len(matching_versions) == 1  # exactly the one real revision, nothing more claimed
