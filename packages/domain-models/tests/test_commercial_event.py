from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain_models import MAX_SEVERITY, MIN_SEVERITY, CommercialEvent


def _base_kwargs(**overrides):
    kwargs = dict(
        event_id="evt_7731",
        project_id="proj_8841",
        trigger_id="trg_2f9a1c",
        severity=1,
    )
    kwargs.update(overrides)
    return kwargs


class TestCommercialEventHappyPath:
    def test_reference_trace_evt_7731_shape(self):
        event = CommercialEvent(**_base_kwargs())
        assert event.event_id == "evt_7731"
        assert event.severity == 1
        assert event.status == "DETECTED"
        assert event.closed_at is None

    @pytest.mark.parametrize(
        "status", ["DETECTED", "TRIAGED", "ACTIONED", "CONTAINED", "CLOSED"]
    )
    def test_accepts_every_status_in_the_progression(self, status):
        event = CommercialEvent(**_base_kwargs(status=status))
        assert event.status == status

    def test_closed_event_carries_closed_at(self):
        event = CommercialEvent(
            **_base_kwargs(
                status="CLOSED",
                closed_at=datetime(2026, 7, 28, 9, 34, 11, tzinfo=timezone.utc),
            )
        )
        assert event.status == "CLOSED"
        assert event.closed_at is not None

    def test_serializes_to_json_and_back(self):
        event = CommercialEvent(**_base_kwargs())
        restored = CommercialEvent.model_validate_json(event.model_dump_json())
        assert restored == event


class TestCommercialEventSeverityBounds:
    @pytest.mark.parametrize("severity", [MIN_SEVERITY, 2, 3, MAX_SEVERITY])
    def test_accepts_severities_in_the_documented_range(self, severity):
        event = CommercialEvent(**_base_kwargs(severity=severity))
        assert event.severity == severity

    def test_rejects_severity_below_minimum(self):
        with pytest.raises(ValidationError):
            CommercialEvent(**_base_kwargs(severity=MIN_SEVERITY - 1))

    def test_rejects_severity_above_maximum(self):
        with pytest.raises(ValidationError):
            CommercialEvent(**_base_kwargs(severity=MAX_SEVERITY + 1))


class TestCommercialEventValidation:
    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            CommercialEvent(**_base_kwargs(status="IN_PROGRESS"))

    def test_rejects_missing_trigger_id(self):
        kwargs = _base_kwargs()
        del kwargs["trigger_id"]
        with pytest.raises(ValidationError):
            CommercialEvent(**kwargs)

    def test_rejects_missing_severity(self):
        kwargs = _base_kwargs()
        del kwargs["severity"]
        with pytest.raises(ValidationError):
            CommercialEvent(**kwargs)

    def test_is_frozen(self):
        event = CommercialEvent(**_base_kwargs())
        with pytest.raises(ValidationError):
            event.severity = 4
