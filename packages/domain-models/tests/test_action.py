import pytest
from pydantic import ValidationError

from domain_models import Action


def _base_kwargs(**overrides):
    kwargs = dict(
        action_id="act_002",
        impact_id="imp_002",
        type="ERP_HOLD_FLAG",
        drafted_content="Hold release-to-fabrication on PO-4471 pending revised duct geometry per RFI-214.",
        status="DRAFTED",
    )
    kwargs.update(overrides)
    return kwargs


class TestActionHappyPath:
    def test_reference_trace_act_002_shape(self):
        action = Action(**_base_kwargs())
        assert action.action_id == "act_002"
        assert action.type == "ERP_HOLD_FLAG"
        assert action.status == "DRAFTED"

    @pytest.mark.parametrize(
        "action_type",
        ["VENDOR_HOLD_NOTICE", "ERP_HOLD_FLAG", "ERP_RESCHEDULE", "FLAG_FOR_REVIEW"],
    )
    def test_accepts_all_four_action_types(self, action_type):
        action = Action(**_base_kwargs(type=action_type))
        assert action.type == action_type

    @pytest.mark.parametrize(
        "status", ["DRAFTED", "APPROVED", "REJECTED", "EDITED", "SENT", "COMPLETED"]
    )
    def test_accepts_every_status_in_the_progression(self, status):
        action = Action(**_base_kwargs(status=status))
        assert action.status == status

    def test_status_defaults_to_drafted(self):
        kwargs = _base_kwargs()
        del kwargs["status"]
        action = Action(**kwargs)
        assert action.status == "DRAFTED"

    def test_serializes_to_json_and_back(self):
        action = Action(**_base_kwargs())
        restored = Action.model_validate_json(action.model_dump_json())
        assert restored == action


class TestActionValidation:
    def test_rejects_invalid_type(self):
        with pytest.raises(ValidationError):
            Action(**_base_kwargs(type="SEND_CARRIER_PIGEON"))

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            Action(**_base_kwargs(status="IN_REVIEW"))

    def test_rejects_empty_drafted_content(self):
        with pytest.raises(ValidationError):
            Action(**_base_kwargs(drafted_content=""))

    def test_rejects_missing_impact_id(self):
        kwargs = _base_kwargs()
        del kwargs["impact_id"]
        with pytest.raises(ValidationError):
            Action(**kwargs)

    def test_is_frozen(self):
        action = Action(**_base_kwargs())
        with pytest.raises(ValidationError):
            action.status = "COMPLETED"
