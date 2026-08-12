"""E.0 — persists/loads a StructuredStateSnapshot to DIP's own derived-data
tree. No database: one JSON file per (document_id, page_index,
extractor_version, ocr_engine, render_scale) — the same file-per-key
persistence style already established by dip.manifest.build (page
manifests keyed by document_id) and dip.ocr.render (render cache keyed by
document_id + page + scale), not a new persistence convention.
"""

from __future__ import annotations

from pathlib import Path

from dip import config
from dip.promote.models import StructuredStateSnapshot


def structured_state_path(
    document_id: str,
    page_index: int,
    extractor_version: str,
    ocr_engine: str,
    render_scale: float,
) -> Path:
    """The one file a given (document, page, extractor_version, ocr_engine,
    render_scale) tuple is always written to and read from. This five-part
    key is the full persistence identity (per the approved plan's E.0
    requirement) — any one part differing produces a different,
    independently-kept file, never an overwrite of another identity's
    snapshot. Mirrors dip.ocr.render.render_cache_path's own
    "<page>_s<scale>.png" convention, extended with the two extra identity
    parts this evidence (unlike a raw render) also depends on."""
    file_name = f"{page_index}_{extractor_version}_{ocr_engine}_s{render_scale}.json"
    return config.STRUCTURED_STATE_DIR / document_id / file_name


def persist_structured_state(snapshot: StructuredStateSnapshot) -> Path:
    """Writes the snapshot to its identity's path, always overwriting
    whatever was previously there. Idempotent in the sense that matters
    here: two calls with an equal snapshot produce byte-identical file
    contents (Pydantic's model_dump_json is a deterministic function of the
    model's field values), not a duplicated or appended entry — there is
    exactly one file per identity, exactly as dip.manifest.build's own
    _persist() behaves for page manifests."""
    path = structured_state_path(
        snapshot.document_id,
        snapshot.page_index,
        snapshot.extractor_version,
        snapshot.ocr_engine,
        snapshot.render_scale,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_structured_state(
    document_id: str,
    page_index: int,
    extractor_version: str,
    ocr_engine: str,
    render_scale: float,
) -> StructuredStateSnapshot | None:
    """Returns None (never raises) if nothing has been persisted yet at this
    exact identity — callers decide whether that absence is an error for
    their own purpose; this function only reports presence/absence,
    exactly as dip.manifest.build.load_manifest does for manifests."""
    path = structured_state_path(document_id, page_index, extractor_version, ocr_engine, render_scale)
    if not path.exists():
        return None
    return StructuredStateSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
