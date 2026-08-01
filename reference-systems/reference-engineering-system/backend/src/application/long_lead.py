from __future__ import annotations

from datetime import date


def is_long_lead(
    lead_time_days: int | None, required_on_site_date: date | None, today: date
) -> bool:
    """The Reference Engineering System doc's own Recommendation #2: flag a
    submittal whose lead_time exceeds the days remaining to its
    required_on_site_date. Neither field being present means "not
    computable," never a false negative dressed up as "not long-lead"."""
    if lead_time_days is None or required_on_site_date is None:
        return False
    days_remaining = (required_on_site_date - today).days
    return lead_time_days > days_remaining
