"""diff_schedule() correctness — fully independent of OCR, using only the
clearly-labeled SYNTHETIC fixtures. No pypdfium2 or OCR import anywhere in
the module under test."""

import json

from dip.diff.engine import diff_schedule
from dip.diff.models import EquipmentRow


def test_matched_tag_with_changed_fields(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    sheet_b, rows_b = synthetic_rev_b
    assert sheet_a == sheet_b

    result = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    changed = {rc.key: rc for rc in result.row_changes if rc.change_type == "changed"}
    assert "AH-9C" in changed
    fields_by_name = {fc.field: fc for fc in changed["AH-9C"].fields}
    assert fields_by_name["fed_from_panel"].before == "MR6"
    assert fields_by_name["fed_from_panel"].after == "MR7"
    assert fields_by_name["mca"].before == "45"
    assert fields_by_name["mca"].after == "60"
    assert fields_by_name["fla"].before == "38"
    assert fields_by_name["fla"].after == "52"


def test_added_row(synthetic_rev_a, synthetic_rev_b):
    _, rows_a = synthetic_rev_a
    sheet_b, rows_b = synthetic_rev_b

    result = diff_schedule(sheet_b, rows_a, rows_b, key_field="tag")

    added = [rc for rc in result.row_changes if rc.change_type == "added"]
    assert {rc.key for rc in added} == {"AH-20"}
    assert added[0].before_evidence is None
    assert added[0].after_evidence is not None


def test_removed_row(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    _, rows_b = synthetic_rev_b

    result = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    removed = [rc for rc in result.row_changes if rc.change_type == "removed"]
    assert {rc.key for rc in removed} == {"AH-3"}
    assert removed[0].after_evidence is None
    assert removed[0].before_evidence is not None


def test_unchanged_row_produces_no_row_change_entry(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    _, rows_b = synthetic_rev_b

    result = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    keys_in_row_changes = {rc.key for rc in result.row_changes}
    assert "AH-11B" not in keys_in_row_changes
    assert result.unchanged_row_count == 1


def test_full_summary_counts(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    _, rows_b = synthetic_rev_b

    result = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    change_types = [rc.change_type for rc in result.row_changes]
    assert change_types.count("changed") == 1
    assert change_types.count("added") == 1
    assert change_types.count("removed") == 1
    assert result.unchanged_row_count == 1
    assert "1 changed" in result.summary
    assert "1 added" in result.summary
    assert "1 removed" in result.summary
    assert "1 unchanged" in result.summary


def test_determinism_same_input_twice_is_byte_identical(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    _, rows_b = synthetic_rev_b

    result_1 = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")
    result_2 = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    dump_1 = json.dumps(result_1.model_dump(mode="json"), sort_keys=True)
    dump_2 = json.dumps(result_2.model_dump(mode="json"), sort_keys=True)
    assert dump_1 == dump_2


def test_row_order_never_affects_output(synthetic_rev_a, synthetic_rev_b):
    sheet_a, rows_a = synthetic_rev_a
    _, rows_b = synthetic_rev_b

    forward = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")
    reversed_input = diff_schedule(sheet_a, list(reversed(rows_a)), list(reversed(rows_b)), key_field="tag")

    assert [rc.key for rc in forward.row_changes] == [rc.key for rc in reversed_input.row_changes]


def test_identical_revisions_produce_zero_changes():
    row = EquipmentRow(
        tag="AH-1",
        fed_from_panel="MR1",
        mca="10",
        fla="8",
        evidence={
            "document_id": "SYNTHETIC",
            "file_name": "SYNTHETIC_FIXTURE_NOT_A_REAL_FILE.json",
            "page_index": 0,
            "extraction_method": "synthetic_fixture",
            "extractor_version": "fixture-0.1.0",
            "extracted_at": "2026-01-01T00:00:00Z",
        },
    )
    result = diff_schedule("SYNTHETIC-DEMO-SCHEDULE", [row], [row], key_field="tag")
    assert result.row_changes == []
    assert result.unchanged_row_count == 1


def test_empty_revisions_produce_empty_result():
    result = diff_schedule("SYNTHETIC-DEMO-SCHEDULE", [], [], key_field="tag")
    assert result.row_changes == []
    assert result.unchanged_row_count == 0


def test_generic_over_a_different_row_model_not_hardcoded_to_equipmentrow():
    """Proves diff_schedule isn't secretly coupled to EquipmentRow's own
    field names — Phase C's future replacement row type just needs a key
    field and comparable fields."""
    from pydantic import BaseModel

    class PanelScheduleRow(BaseModel):
        panel_id: str
        supply_from: str | None = None
        evidence: dict | None = None

    a = [PanelScheduleRow(panel_id="MR1", supply_from="MRDP")]
    b = [PanelScheduleRow(panel_id="MR1", supply_from="MRDP2")]

    result = diff_schedule("SYNTHETIC-PANEL-DEMO", a, b, key_field="panel_id")

    assert len(result.row_changes) == 1
    assert result.row_changes[0].key == "MR1"
    assert result.row_changes[0].fields[0].field == "supply_from"
    assert result.row_changes[0].fields[0].before == "MRDP"
    assert result.row_changes[0].fields[0].after == "MRDP2"
