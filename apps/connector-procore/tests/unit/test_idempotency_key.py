"""Pure-logic unit test — no database, no network.

Reference Execution Trace Phase 1.1: the idempotency cache key is the
(resource_id, event_type, timestamp) triple (plus resource_name, since a
connector may one day handle more than one resource type on one project)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from idempotency.cache import build_cache_key


def test_cache_key_is_stable_for_identical_inputs():
    key1 = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:14:03Z")
    key2 = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:14:03Z")
    assert key1 == key2


def test_cache_key_differs_on_resource_id():
    key1 = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:14:03Z")
    key2 = build_cache_key("rfis", 9999999, "update", "2026-07-28T09:14:03Z")
    assert key1 != key2


def test_cache_key_differs_on_timestamp():
    key1 = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:14:03Z")
    key2 = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:15:00Z")
    assert key1 != key2


def test_cache_key_matches_expected_format():
    key = build_cache_key("rfis", 4821356, "update", "2026-07-28T09:14:03Z")
    assert key == "rfis:4821356:update:2026-07-28T09:14:03Z"
