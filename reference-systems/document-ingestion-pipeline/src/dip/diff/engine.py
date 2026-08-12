"""diff_schedule() — the one pure function Phase D exists to prove.

No I/O, no OCR, no pypdfium2 import anywhere in this module — deliberately,
per the instruction to prove the mechanism independent of OCR. Deterministic:
same two inputs always produce byte-identical output (rows are sorted by key,
never left in dict/insertion order).

Generic over any Pydantic BaseModel row type, not hardcoded to EquipmentRow —
callers name the key field and which fields to compare, so a future
panel-schedule or one-line-diagram row type reuses this unchanged.
"""

from __future__ import annotations

from pydantic import BaseModel

from dip.diff.models import DetectedChange, FieldChange, RowChange


def diff_schedule(
    sheet: str,
    rev_a: list[BaseModel],
    rev_b: list[BaseModel],
    key_field: str,
    compare_fields: list[str] | None = None,
    evidence_field: str = "evidence",
) -> DetectedChange:
    if not rev_a and not rev_b:
        return DetectedChange(sheet=sheet, key_field=key_field, row_changes=[], unchanged_row_count=0, summary=f"{sheet}: no rows in either revision")

    sample = (rev_a or rev_b)[0]
    all_fields = list(type(sample).model_fields.keys())
    if compare_fields is None:
        compare_fields = sorted(f for f in all_fields if f not in (key_field, evidence_field))

    def _dump(row: BaseModel) -> dict:
        return row.model_dump(mode="json")

    a_by_key = {getattr(row, key_field): row for row in rev_a}
    b_by_key = {getattr(row, key_field): row for row in rev_b}

    row_changes: list[RowChange] = []
    unchanged_row_count = 0

    for key in sorted(set(a_by_key) - set(b_by_key)):
        row = a_by_key[key]
        row_changes.append(
            RowChange(
                key=key,
                change_type="removed",
                fields=[],
                before_evidence=getattr(row, evidence_field, None),
                after_evidence=None,
            )
        )

    for key in sorted(set(b_by_key) - set(a_by_key)):
        row = b_by_key[key]
        row_changes.append(
            RowChange(
                key=key,
                change_type="added",
                fields=[],
                before_evidence=None,
                after_evidence=getattr(row, evidence_field, None),
            )
        )

    for key in sorted(set(a_by_key) & set(b_by_key)):
        row_a = a_by_key[key]
        row_b = b_by_key[key]
        dump_a, dump_b = _dump(row_a), _dump(row_b)

        field_changes = [
            FieldChange(field=field, before=dump_a.get(field), after=dump_b.get(field))
            for field in compare_fields
            if dump_a.get(field) != dump_b.get(field)
        ]

        if field_changes:
            row_changes.append(
                RowChange(
                    key=key,
                    change_type="changed",
                    fields=field_changes,
                    before_evidence=getattr(row_a, evidence_field, None),
                    after_evidence=getattr(row_b, evidence_field, None),
                )
            )
        else:
            unchanged_row_count += 1

    row_changes.sort(key=lambda rc: (rc.key, rc.change_type))

    n_changed = sum(1 for rc in row_changes if rc.change_type == "changed")
    n_added = sum(1 for rc in row_changes if rc.change_type == "added")
    n_removed = sum(1 for rc in row_changes if rc.change_type == "removed")
    summary = (
        f"{sheet}: {n_changed} changed, {n_added} added, {n_removed} removed, "
        f"{unchanged_row_count} unchanged"
    )

    return DetectedChange(
        sheet=sheet,
        key_field=key_field,
        row_changes=row_changes,
        unchanged_row_count=unchanged_row_count,
        summary=summary,
    )
