from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain_models import Approval


def _base_kwargs(**overrides):
    kwargs = dict(
        approval_id="apr_001",
        action_id="act_001",
        user_id="user_2209",
        decision="APPROVED",
        edited_content=None,
        decided_at=datetime(2026, 7, 28, 9, 21, 44, tzinfo=timezone.utc),
    )
    kwargs.update(overrides)
    return kwargs


class TestApprovalHappyPath:
    def test_reference_trace_apr_001_shape(self):
        approval = Approval(**_base_kwargs())
        assert approval.approval_id == "apr_001"
        assert approval.decision == "APPROVED"
        assert approval.edited_content is None

    @pytest.mark.parametrize("decision", ["APPROVED", "REJECTED", "ACKNOWLEDGED_NO_ACTION"])
    def test_accepts_all_three_decisions(self, decision):
        approval = Approval(**_base_kwargs(decision=decision))
        assert approval.decision == decision

    def test_acknowledged_no_action_reference_trace_apr_004_shape(self):
        approval = Approval(
            approval_id="apr_004",
            action_id="act_004",
            user_id="user_2209",
            decision="ACKNOWLEDGED_NO_ACTION",
            decided_at=datetime(2026, 7, 28, 9, 34, 10, tzinfo=timezone.utc),
        )
        assert approval.decision == "ACKNOWLEDGED_NO_ACTION"
        assert approval.edited_content is None

    def test_edited_content_captures_pre_approval_edits(self):
        approval = Approval(**_base_kwargs(edited_content="Changed hold window to 10 days."))
        assert approval.edited_content == "Changed hold window to 10 days."

    def test_decided_at_is_optional_and_service_assigned(self):
        kwargs = _base_kwargs()
        del kwargs["decided_at"]
        approval = Approval(**kwargs)
        assert approval.decided_at is None

    def test_serializes_to_json_and_back(self):
        approval = Approval(**_base_kwargs())
        restored = Approval.model_validate_json(approval.model_dump_json())
        assert restored == approval


class TestApprovalValidation:
    def test_rejects_invalid_decision(self):
        with pytest.raises(ValidationError):
            Approval(**_base_kwargs(decision="MAYBE_LATER"))

    def test_rejects_missing_user_id(self):
        kwargs = _base_kwargs()
        del kwargs["user_id"]
        with pytest.raises(ValidationError):
            Approval(**kwargs)

    def test_rejects_empty_action_id(self):
        with pytest.raises(ValidationError):
            Approval(**_base_kwargs(action_id=""))

    def test_is_frozen(self):
        approval = Approval(**_base_kwargs())
        with pytest.raises(ValidationError):
            approval.decision = "REJECTED"
