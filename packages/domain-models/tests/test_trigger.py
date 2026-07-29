from datetime import datetime, timezone

import pytest
from envelope_schemas import DrawingRef
from pydantic import ValidationError

from domain_models import TRIGGER_STATUS_PENDING_RESOLUTION, Trigger


def _base_kwargs(**overrides):
    kwargs = dict(
        trigger_id="trg_2f9a1c",
        project_id="proj_8841",
        type="RFI_APPROVED",
        source_envelope_ref="env_9a41bb",
        spec_section_refs=["23 31 13"],
        drawing_refs=[DrawingRef(item_id="doc_M-2.1", version_id="rev_C")],
        location_refs=["Level 4, Grid B-4"],
        raw_document_ref="procore://attachments/991211",
        occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
    )
    kwargs.update(overrides)
    return kwargs


class TestTriggerHappyPath:
    def test_reference_trace_phase_2_3_shape(self):
        trigger = Trigger(**_base_kwargs())
        assert trigger.trigger_id == "trg_2f9a1c"
        assert trigger.project_id == "proj_8841"
        assert trigger.type == "RFI_APPROVED"
        assert trigger.source_envelope_ref == "env_9a41bb"
        assert trigger.status == TRIGGER_STATUS_PENDING_RESOLUTION

    def test_status_defaults_to_pending_resolution(self):
        trigger = Trigger(**_base_kwargs())
        assert trigger.status == "PENDING_RESOLUTION"

    @pytest.mark.parametrize("event_type", ["RFI_APPROVED", "DRAWING_REVISED", "SPEC_UPDATED"])
    def test_accepts_all_three_trigger_types(self, event_type):
        trigger = Trigger(**_base_kwargs(type=event_type))
        assert trigger.type == event_type

    def test_created_at_is_optional_and_service_assigned(self):
        trigger = Trigger(**_base_kwargs())
        assert trigger.created_at is None
        stamped = Trigger(**_base_kwargs(created_at=datetime(2026, 7, 28, 9, 14, 7, tzinfo=timezone.utc)))
        assert stamped.created_at is not None

    def test_serializes_to_json_and_back(self):
        trigger = Trigger(**_base_kwargs())
        restored = Trigger.model_validate_json(trigger.model_dump_json())
        assert restored == trigger


class TestTriggerValidation:
    def test_rejects_invalid_type(self):
        with pytest.raises(ValidationError):
            Trigger(**_base_kwargs(type="NOT_A_REAL_TYPE"))

    def test_rejects_empty_trigger_id(self):
        with pytest.raises(ValidationError):
            Trigger(**_base_kwargs(trigger_id=""))

    def test_rejects_empty_project_id(self):
        with pytest.raises(ValidationError):
            Trigger(**_base_kwargs(project_id=""))

    def test_rejects_missing_occurred_at(self):
        kwargs = _base_kwargs()
        del kwargs["occurred_at"]
        with pytest.raises(ValidationError):
            Trigger(**kwargs)

    def test_is_frozen(self):
        trigger = Trigger(**_base_kwargs())
        with pytest.raises(ValidationError):
            trigger.status = "SOMETHING_ELSE"
