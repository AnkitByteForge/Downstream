from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from connector_interface import ActionPayload, ConnectionHealth, DispatchReceipt


def _payload_kwargs(**overrides):
    kwargs = dict(
        action_id="act_001",
        action_type="VENDOR_HOLD_NOTICE",
        drafted_content="Arjun Steelworks — hanger steel shipped against PO-4488 ...",
        target_artifact_ref="po_4488",
        idempotency_key="act_001-dispatch-1",
    )
    kwargs.update(overrides)
    return kwargs


class TestActionPayload:
    def test_reference_trace_phase_11_3_shape(self):
        payload = ActionPayload(**_payload_kwargs())
        assert payload.action_id == "act_001"
        assert payload.idempotency_key == "act_001-dispatch-1"

    @pytest.mark.parametrize(
        "action_type",
        ["VENDOR_HOLD_NOTICE", "ERP_HOLD_FLAG", "ERP_RESCHEDULE", "FLAG_FOR_REVIEW"],
    )
    def test_accepts_all_four_action_types(self, action_type):
        payload = ActionPayload(**_payload_kwargs(action_type=action_type))
        assert payload.action_type == action_type

    def test_rejects_invalid_action_type(self):
        with pytest.raises(ValidationError):
            ActionPayload(**_payload_kwargs(action_type="SEND_CARRIER_PIGEON"))

    def test_rejects_empty_idempotency_key(self):
        with pytest.raises(ValidationError):
            ActionPayload(**_payload_kwargs(idempotency_key=""))

    def test_is_frozen(self):
        payload = ActionPayload(**_payload_kwargs())
        with pytest.raises(ValidationError):
            payload.action_id = "act_999"

    def test_serializes_to_json_and_back(self):
        payload = ActionPayload(**_payload_kwargs())
        restored = ActionPayload.model_validate_json(payload.model_dump_json())
        assert restored == payload


class TestDispatchReceipt:
    def test_reference_trace_phase_11_3_shape(self):
        receipt = DispatchReceipt(dispatch_id="disp_5510", status="SENT")
        assert receipt.dispatch_id == "disp_5510"
        assert receipt.status == "SENT"
        assert receipt.detail is None

    @pytest.mark.parametrize("status", ["SENT", "DELIVERED", "FAILED"])
    def test_accepts_all_three_statuses(self, status):
        receipt = DispatchReceipt(dispatch_id="disp_1", status=status)
        assert receipt.status == status

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            DispatchReceipt(dispatch_id="disp_1", status="PENDING")

    def test_failed_receipt_can_carry_a_detail_message(self):
        receipt = DispatchReceipt(dispatch_id="disp_1", status="FAILED", detail="SMTP timeout")
        assert receipt.detail == "SMTP timeout"

    def test_is_frozen(self):
        receipt = DispatchReceipt(dispatch_id="disp_1", status="SENT")
        with pytest.raises(ValidationError):
            receipt.status = "FAILED"


class TestConnectionHealth:
    def test_healthy_connection_has_no_error_state(self):
        health = ConnectionHealth(
            source_system="procore",
            scope_granted="partial:[rfis,submittals,documents]",
            last_successful_sync=datetime(2026, 7, 28, 9, 14, tzinfo=timezone.utc),
        )
        assert health.error_state is None

    def test_unhealthy_connection_carries_error_state(self):
        health = ConnectionHealth(
            source_system="sap",
            scope_granted="full",
            error_state="401 Unauthorized: OAuth token expired",
        )
        assert health.error_state is not None

    def test_last_successful_sync_is_optional(self):
        health = ConnectionHealth(source_system="sap", scope_granted="full")
        assert health.last_successful_sync is None

    def test_rejects_missing_scope_granted(self):
        with pytest.raises(ValidationError):
            ConnectionHealth(source_system="sap")

    def test_is_frozen(self):
        health = ConnectionHealth(source_system="sap", scope_granted="full")
        with pytest.raises(ValidationError):
            health.scope_granted = "partial"
