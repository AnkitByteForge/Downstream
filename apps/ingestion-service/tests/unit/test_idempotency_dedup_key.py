from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from repository.idempotency_repository import build_dedup_key

OCCURRED_AT = datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)


def test_dedup_key_format():
    key = build_dedup_key("procore", "4821356", OCCURRED_AT)
    assert key == "procore:4821356:2026-07-28T09:14:03+00:00"


def test_dedup_key_differs_on_source_id():
    assert build_dedup_key("procore", "1", OCCURRED_AT) != build_dedup_key("procore", "2", OCCURRED_AT)
