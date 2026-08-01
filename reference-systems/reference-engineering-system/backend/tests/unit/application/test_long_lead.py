from __future__ import annotations

from datetime import date

from application.long_lead import is_long_lead


def test_none_lead_time_is_not_computable():
    assert is_long_lead(None, date(2026, 11, 2), date(2026, 8, 1)) is False


def test_none_required_date_is_not_computable():
    assert is_long_lead(84, None, date(2026, 8, 1)) is False


def test_lead_time_exceeding_days_remaining_is_long_lead():
    # required 2026-11-02, today 2026-08-20 -> 74 days remaining, lead_time 84
    assert is_long_lead(84, date(2026, 11, 2), date(2026, 8, 20)) is True


def test_lead_time_within_days_remaining_is_not_long_lead():
    assert is_long_lead(30, date(2026, 11, 2), date(2026, 8, 1)) is False
