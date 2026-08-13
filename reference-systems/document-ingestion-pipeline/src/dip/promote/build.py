"""E.6 -- the promotion orchestrator. VALID structured evidence -> RES
Drawing/DrawingVersion API.

    structured_state (E.0, unfiltered evidence)
        -> valid_facts_view (E.1: VALID-only, no implicit validation)
            -> RES create_drawing / create_drawing_version (E.5 client)

Only fields whose field_validation status is exactly "VALID" ever leave
this module. AMBIGUOUS, INVALID, MISSING, and fields with no recorded
validation status at all (e.g. `tag`, `existing_designation`) are excluded
by dip.promote.filter.valid_facts_view before this module ever sees them
-- this module does not re-implement that rule, it depends on it, so
there is exactly one place that rule lives.

RES receives only the engineering-domain representation required to
create the Drawing/DrawingVersion plus the opaque source_evidence_ref
pointer -- never OCR confidence, bounding boxes, or any other DIP-internal
detail. The full evidence stays in DIP's own structured_state; RES stores
only a pointer back to it (ADR-009).
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from dip import config
from dip.promote.filter import ValidatedFieldFact, valid_facts_view
from dip.promote.models import StructuredStateSnapshot
from dip.promote.res_client import ResClientError, ResPromotionClient

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.0

PromotionOutcome = Literal["SUCCESS", "FAILED"]


def evidence_ref_uri(document_id: str, page_index: int, field_name: str, tag: str) -> str:
    """The one place this opaque URI shape is constructed. RES itself never
    parses this string (ADR-009) -- it exists purely so DIP can resolve a
    RevisionCloud.source_evidence_ref back to the exact evidence it came
    from."""
    return f"dip://document/{document_id}/page/{page_index}/field/{field_name}?row={tag}"


_EVIDENCE_REF_PATTERN = re.compile(
    r"^dip://document/(?P<document_id>[^/]+)/page/(?P<page_index>\d+)/field/(?P<field_name>[^?]+)\?row=(?P<tag>.+)$"
)


def parse_evidence_ref_uri(uri: str) -> dict[str, str | int]:
    """The inverse of evidence_ref_uri -- proves the pointer RES stores is
    genuinely resolvable back into DIP's own evidence identity (document_id,
    page_index, field_name, tag), not just a visually plausible string. DIP
    is the only party that ever calls this; RES never does (ADR-009)."""
    match = _EVIDENCE_REF_PATTERN.match(uri)
    if not match:
        raise ValueError(f"Not a recognized DIP evidence_ref URI: {uri!r}")
    return {
        "document_id": match.group("document_id"),
        "page_index": int(match.group("page_index")),
        "field_name": match.group("field_name"),
        "tag": match.group("tag"),
    }


def _revision_clouds_for_facts(
    document_id: str, page_index: int, facts: list[ValidatedFieldFact]
) -> list[dict]:
    """Builds RES's RevisionCloudIn-shaped dicts from the promotion-eligible
    facts, in a DETERMINISTIC order (sorted by (tag, field_name), never
    insertion order which can vary run to run) so that two promotions of
    the same snapshot always produce byte-identical request bodies --
    this determinism is what makes create_drawing_version's idempotent
    retry behavior (E.4) meaningful rather than coincidental."""
    ordered = sorted(facts, key=lambda f: (f.tag, f.field_name))
    return [
        {
            "area": f"New Unit block, row {f.tag}",
            "delta_number": i + 1,
            "description": f"{f.field_name} = {f.raw_value}",
            "source_evidence_ref": evidence_ref_uri(document_id, page_index, f.field_name, f.tag),
        }
        for i, f in enumerate(ordered)
    ]


@dataclass(frozen=True)
class PromotionAttemptRecord:
    """One append-only audit entry. Traces a promotion attempt to its
    exact source evidence identity, its target RES resource, and its
    result -- per the approved plan's auditability requirement. This is
    NOT a second system of record for the promoted facts themselves (those
    live in RES, per ADR-009); it only records that DIP attempted to
    promote them, when, and with what outcome."""

    attempted_at: str  # ISO 8601 UTC
    document_id: str
    page_index: int
    extractor_version: str
    ocr_engine: str
    render_scale: float
    target_project_id: int
    sheet_number: str
    revision_label: str
    promoted_fields: list[tuple[str, str]]  # [(tag, field_name), ...], the exact facts attempted
    outcome: PromotionOutcome
    drawing_id: int | None = None
    drawing_version_id: int | None = None
    attempts_made: int = 1
    error: str | None = None

    def to_json_line(self) -> str:
        return json.dumps(
            {
                "attempted_at": self.attempted_at,
                "document_id": self.document_id,
                "page_index": self.page_index,
                "extractor_version": self.extractor_version,
                "ocr_engine": self.ocr_engine,
                "render_scale": self.render_scale,
                "target_project_id": self.target_project_id,
                "sheet_number": self.sheet_number,
                "revision_label": self.revision_label,
                "promoted_fields": [list(pair) for pair in self.promoted_fields],
                "outcome": self.outcome,
                "drawing_id": self.drawing_id,
                "drawing_version_id": self.drawing_version_id,
                "attempts_made": self.attempts_made,
                "error": self.error,
            }
        )


@dataclass(frozen=True)
class PromotionResult:
    drawing: dict
    drawing_version: dict
    promoted_facts: list[ValidatedFieldFact]
    attempt: PromotionAttemptRecord


def promotion_log_path(document_id: str) -> Path:
    return config.PROMOTION_LOG_DIR / f"{document_id}.jsonl"


def _append_attempt_record(record: PromotionAttemptRecord) -> None:
    path = promotion_log_path(record.document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(record.to_json_line() + "\n")


def _call_with_bounded_retry(
    fn: Callable[[], dict],
    *,
    max_attempts: int,
    backoff_base_seconds: float,
    sleep: Callable[[float], None],
) -> tuple[dict, int]:
    """Retries only ResClientError instances whose .retryable is True
    (connection errors, timeouts, 5xx) -- a non-retryable error (bad
    credentials, a malformed 4xx request) is raised immediately, since
    retrying it can never succeed. Bounded: after max_attempts, the last
    error is raised rather than retried forever."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn(), attempt
        except ResClientError as exc:
            if not exc.retryable or attempt >= max_attempts:
                raise
            delay = backoff_base_seconds * (2 ** (attempt - 1))
            sleep(delay)


def promote_snapshot(
    snapshot: StructuredStateSnapshot,
    client: ResPromotionClient,
    *,
    target_project_id: int,
    sheet_number: str,
    drawing_title: str,
    discipline_code: str,
    revision_label: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
    sleep: Callable[[float], None] | None = None,
    now: Callable[[], datetime] | None = None,
) -> PromotionResult:
    """Promotes exactly the VALID facts in `snapshot` into RES, as one
    Drawing + one DrawingVersion.

    Identity is entirely explicit, never inferred: `target_project_id`,
    `sheet_number`, and `revision_label` are supplied by the caller (E.7),
    not derived from OCR-run metadata (extractor_version/ocr_engine/
    render_scale describe *how* the evidence was extracted, not *which
    real drawing revision* it represents -- that is domain knowledge only
    a caller with the actual document in hand can supply). Re-running this
    function with the same snapshot and the same identity arguments is
    safe: create_drawing/create_drawing_version are idempotent on RES's
    side (E.4, DB-level UNIQUE constraints), and the revision_clouds this
    function builds are a deterministic function of the snapshot's own
    VALID facts (sorted, never insertion-order-dependent) -- so a retried
    promotion sends byte-identical requests and RES returns the same rows,
    never a duplicate DrawingVersion.

    Never silently discards a failure: on an unretryable or
    retries-exhausted error, a FAILED attempt record is still appended to
    the audit log before the exception is re-raised.
    """
    sleep = sleep or time.sleep
    now = now or (lambda: datetime.now(timezone.utc))

    facts = valid_facts_view(snapshot)
    revision_clouds = _revision_clouds_for_facts(snapshot.document_id, snapshot.page_index, facts)
    promoted_fields = sorted({(f.tag, f.field_name) for f in facts})

    def _base_record(*, outcome: PromotionOutcome, **overrides) -> PromotionAttemptRecord:
        return PromotionAttemptRecord(
            attempted_at=now().isoformat(),
            document_id=snapshot.document_id,
            page_index=snapshot.page_index,
            extractor_version=snapshot.extractor_version,
            ocr_engine=snapshot.ocr_engine,
            render_scale=snapshot.render_scale,
            target_project_id=target_project_id,
            sheet_number=sheet_number,
            revision_label=revision_label,
            promoted_fields=promoted_fields,
            outcome=outcome,
            **overrides,
        )

    total_attempts = 0
    try:
        drawing, attempts_a = _call_with_bounded_retry(
            lambda: client.create_drawing(target_project_id, sheet_number, drawing_title, discipline_code),
            max_attempts=max_attempts,
            backoff_base_seconds=backoff_base_seconds,
            sleep=sleep,
        )
        total_attempts += attempts_a

        version, attempts_b = _call_with_bounded_retry(
            lambda: client.create_drawing_version(
                target_project_id, drawing["id"], revision_label, discipline_code, revision_clouds
            ),
            max_attempts=max_attempts,
            backoff_base_seconds=backoff_base_seconds,
            sleep=sleep,
        )
        total_attempts += attempts_b
    except ResClientError as exc:
        _append_attempt_record(_base_record(outcome="FAILED", attempts_made=max(total_attempts, 1), error=str(exc)))
        raise

    record = _base_record(
        outcome="SUCCESS",
        drawing_id=drawing["id"],
        drawing_version_id=version["id"],
        attempts_made=total_attempts,
        error=None,
    )
    _append_attempt_record(record)

    return PromotionResult(drawing=drawing, drawing_version=version, promoted_facts=facts, attempt=record)
