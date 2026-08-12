#!/usr/bin/env python
"""CLI: run diff_schedule() against the two SYNTHETIC fixtures and write the
result for inspection. Produces no claim about real DSH-Atascadero data —
see the fixtures' own "SYNTHETIC"/"disclaimer" fields.

Usage:
    python scripts/run_synthetic_diff_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dip import config  # noqa: E402
from dip.diff.engine import diff_schedule  # noqa: E402
from dip.diff.models import EquipmentRow  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def _load(file_name: str) -> tuple[str, list[EquipmentRow]]:
    payload = json.loads((FIXTURES_DIR / file_name).read_text(encoding="utf-8"))
    assert payload["SYNTHETIC"] is True
    return payload["sheet"], [EquipmentRow.model_validate(r) for r in payload["rows"]]


def main() -> None:
    sheet_a, rows_a = _load("synthetic_rev_a.json")
    sheet_b, rows_b = _load("synthetic_rev_b.json")
    assert sheet_a == sheet_b

    result = diff_schedule(sheet_a, rows_a, rows_b, key_field="tag")

    config.DETECTED_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.DETECTED_CHANGES_DIR / "synthetic_demo.json"
    out_path.write_text(
        json.dumps(
            {
                "SYNTHETIC": True,
                "disclaimer": "Output of diffing two SYNTHETIC fixtures. Proves the Phase D mechanism only — not real DSH-Atascadero evidence.",
                "detected_change": result.model_dump(mode="json"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")
    print(result.summary)


if __name__ == "__main__":
    main()
