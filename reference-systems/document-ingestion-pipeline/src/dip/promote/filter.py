"""E.1 — the VALID-only, promotion-eligible view over a
StructuredStateSnapshot's already-persisted evidence.

This is a DERIVED READ, not a second store: nothing here is ever written
to disk. Per the approved plan, "do not create a second source-of-truth
file for validated facts" — this module recomputes its answer from
snapshot.rows[*].field_validation on every call, so it can never drift out
of sync with the underlying evidence, and it never mutates the
EquipmentRow objects it reads. Filtering only ever *omits* a field from
the returned view; it never edits a raw or normalized value, and the
underlying snapshot (and its file on disk) is untouched by calling this.

Eligibility rule — exact, no exceptions, per the approved plan's E.1 rules:
    field_validation[field] == "VALID"        -> eligible
    "AMBIGUOUS" / "INVALID" / "MISSING"        -> never eligible
    field absent from field_validation at all  -> never eligible

The last case matters: EquipmentRow.tag and .existing_designation never
get a validator run against them at all (Phase C's field_validation only
covers the six New Unit fields normalize.py has dedicated validators for —
see dip.diff.models.EquipmentRow's own docstring). Absence of a validation
verdict is not the same as a VALID verdict and must not be treated as one
— an unvalidated field is exactly as promotion-ineligible as an explicitly
AMBIGUOUS one.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from dip.diff.models import EquipmentRow
from dip.promote.models import StructuredStateSnapshot


class ValidatedFieldFact(BaseModel):
    """One promotion-eligible field, still carrying its own row identity —
    filtering never strips information, it only decides which fields are
    allowed through the view at all."""

    model_config = ConfigDict(frozen=True)

    tag: str
    field_name: str
    raw_value: str
    normalized_value: float | None = None


def valid_fields_for_row(row: EquipmentRow) -> list[ValidatedFieldFact]:
    """Every field on one row whose field_validation status is exactly
    "VALID". Never raises, never mutates `row` — a pure filter over data
    that already exists on it."""
    facts: list[ValidatedFieldFact] = []
    for field_name, status in row.field_validation.items():
        if status != "VALID":
            continue
        raw_value = getattr(row, field_name, None)
        if raw_value is None:
            # A VALID status should imply non-empty raw text (validators
            # return MISSING for a genuinely empty cell) — this branch is
            # not expected to be reachable, but a null value is never
            # trusted to promote regardless of what field_validation says.
            continue
        normalized_value = getattr(row, f"{field_name}_numeric", None)
        facts.append(
            ValidatedFieldFact(
                tag=row.tag,
                field_name=field_name,
                raw_value=raw_value,
                normalized_value=normalized_value,
            )
        )
    return facts


def valid_facts_view(snapshot: StructuredStateSnapshot) -> list[ValidatedFieldFact]:
    """The full promotion-eligible view over one persisted snapshot — every
    VALID field, across every row. Zero AMBIGUOUS / INVALID / MISSING /
    unvalidated fields are ever included (safety-property tested in
    tests/unit/test_promote_filter.py and, against real E0.4 evidence, in
    tests/golden/test_promote_against_real_e04.py)."""
    facts: list[ValidatedFieldFact] = []
    for row in snapshot.rows:
        facts.extend(valid_fields_for_row(row))
    return facts
