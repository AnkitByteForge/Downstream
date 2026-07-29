from datetime import datetime, timezone

import pytest
from envelope_schemas import CommercialArtifactSnapshot, EngineeringEventEnvelope

from connector_interface import (
    ActionPayload,
    ConnectionHealth,
    ConnectorInterface,
    DispatchReceipt,
)


class TestConnectorInterfaceIsAbstract:
    def test_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            ConnectorInterface()  # type: ignore[abstract]

    @pytest.mark.parametrize(
        "missing_method",
        [
            "fetch_engineering_events",
            "fetch_artifact_snapshot",
            "push_action",
            "health_check",
        ],
    )
    def test_partial_implementations_cannot_be_instantiated(self, missing_method):
        """A subclass implementing only three of the four abstract methods
        must still fail to instantiate — every adapter, wired or stub, is
        required to implement the full interface (docs/07 §3's connector
        template: 'every adapter implements the shared connector-interface
        package, never its own bespoke contract')."""
        methods = {
            "fetch_engineering_events": lambda self, since: [],
            "fetch_artifact_snapshot": lambda self, artifact_ref: None,
            "push_action": lambda self, action: None,
            "health_check": lambda self: None,
        }
        del methods[missing_method]
        Partial = type("Partial", (ConnectorInterface,), methods)
        with pytest.raises(TypeError):
            Partial()


class _InMemoryConnector(ConnectorInterface):
    """A minimal, fully-conforming implementation used only to prove the
    interface is genuinely implementable and that its method signatures are
    usable end to end. Not a real adapter — no service logic here."""

    def __init__(self) -> None:
        self._events: list[EngineeringEventEnvelope] = []
        self._snapshots: dict[str, CommercialArtifactSnapshot] = {}

    def fetch_engineering_events(self, since: str) -> list[EngineeringEventEnvelope]:
        return list(self._events)

    def fetch_artifact_snapshot(self, artifact_ref: str) -> CommercialArtifactSnapshot:
        return self._snapshots[artifact_ref]

    def push_action(self, action: ActionPayload) -> DispatchReceipt:
        return DispatchReceipt(dispatch_id=f"disp_{action.action_id}", status="SENT")

    def health_check(self) -> ConnectionHealth:
        return ConnectionHealth(source_system="in-memory-test-double", scope_granted="full")


class TestConnectorInterfaceConformingImplementation:
    def test_fetch_engineering_events_returns_envelopes(self):
        connector = _InMemoryConnector()
        connector._events.append(
            EngineeringEventEnvelope(
                source_system="procore",
                source_id="4821356",
                type="RFI_APPROVED",
                occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
            )
        )
        events = connector.fetch_engineering_events(since="cursor-0")
        assert len(events) == 1
        assert events[0].source_id == "4821356"

    def test_fetch_artifact_snapshot_returns_snapshot(self):
        connector = _InMemoryConnector()
        connector._snapshots["po_4471"] = CommercialArtifactSnapshot(
            source_system="sap",
            source_id="4500018823",
            artifact_type="PO",
            project_ref="proj_8841",
        )
        snapshot = connector.fetch_artifact_snapshot("po_4471")
        assert snapshot.source_id == "4500018823"

    def test_push_action_returns_dispatch_receipt(self):
        connector = _InMemoryConnector()
        receipt = connector.push_action(
            ActionPayload(
                action_id="act_001",
                action_type="VENDOR_HOLD_NOTICE",
                drafted_content="Hold notice content.",
                target_artifact_ref="po_4488",
                idempotency_key="act_001-dispatch-1",
            )
        )
        assert receipt.status == "SENT"
        assert receipt.dispatch_id == "disp_act_001"

    def test_health_check_returns_connection_health(self):
        connector = _InMemoryConnector()
        health = connector.health_check()
        assert health.error_state is None
        assert health.scope_granted == "full"

    def test_is_a_connector_interface_instance(self):
        connector = _InMemoryConnector()
        assert isinstance(connector, ConnectorInterface)
