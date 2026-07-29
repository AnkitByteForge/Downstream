from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from event_contracts import (
    ActionApproved,
    ActionConfirmed,
    ActionDispatched,
    ActionDrafted,
    EventClosed,
    EventCreated,
    ImpactTiered,
    KeyCandidate,
    KeysResolved,
    SeverityComputed,
    TriggerDetected,
)


class TestTriggerDetected:
    def test_reference_trace_phase_2_4_shape(self):
        msg = TriggerDetected(
            trigger_id="trg_2f9a1c",
            project_id="proj_8841",
            occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
        )
        assert msg.trigger_id == "trg_2f9a1c"
        assert msg.project_id == "proj_8841"

    def test_rejects_missing_project_id(self):
        with pytest.raises(ValidationError):
            TriggerDetected(
                trigger_id="trg_2f9a1c",
                occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
            )

    def test_is_frozen(self):
        msg = TriggerDetected(
            trigger_id="trg_2f9a1c",
            project_id="proj_8841",
            occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
        )
        with pytest.raises(ValidationError):
            msg.trigger_id = "other"


class TestKeysResolved:
    def test_reference_trace_phase_3_shape(self):
        msg = KeysResolved(
            trigger_id="trg_2f9a1c",
            candidates=[
                KeyCandidate(artifact_ref="po_4471", match_basis="cost_code_exact", match_score=0.98),
                KeyCandidate(
                    artifact_ref="po_4488",
                    match_basis="graph_edge:structural_dependency",
                    match_score=0.71,
                ),
                KeyCandidate(
                    artifact_ref="sched_3410",
                    match_basis="graph_edge:location_adjacency",
                    match_score=0.44,
                ),
            ],
        )
        assert len(msg.candidates) == 3
        assert msg.candidates[0].match_score == 0.98

    def test_candidates_default_to_empty_list(self):
        msg = KeysResolved(trigger_id="trg_2f9a1c")
        assert msg.candidates == []

    def test_rejects_match_score_above_one(self):
        with pytest.raises(ValidationError):
            KeyCandidate(artifact_ref="po_4471", match_basis="cost_code_exact", match_score=1.5)

    def test_rejects_negative_match_score(self):
        with pytest.raises(ValidationError):
            KeyCandidate(artifact_ref="po_4471", match_basis="cost_code_exact", match_score=-0.1)


class TestEventCreated:
    def test_reference_trace_phase_8_shape(self):
        msg = EventCreated(project_id="proj_8841", event_id="evt_7731", severity=1)
        assert msg.severity == 1

    def test_rejects_severity_out_of_range(self):
        with pytest.raises(ValidationError):
            EventCreated(project_id="proj_8841", event_id="evt_7731", severity=5)


class TestImpactTiered:
    def test_reference_trace_phase_6_shape(self):
        msg = ImpactTiered(impact_id="imp_002", tier="CERTAIN", severity=2)
        assert msg.tier == "CERTAIN"

    def test_rejects_invalid_tier(self):
        with pytest.raises(ValidationError):
            ImpactTiered(impact_id="imp_002", tier="LIKELY", severity=2)


class TestSeverityComputed:
    def test_reference_trace_phase_6_shape(self):
        msg = SeverityComputed(event_id="evt_7731", severity=1)
        assert msg.event_id == "evt_7731"
        assert msg.severity == 1


class TestActionDrafted:
    def test_reference_trace_phase_6_shape(self):
        msg = ActionDrafted(action_id="act_001")
        assert msg.action_id == "act_001"

    def test_rejects_empty_action_id(self):
        with pytest.raises(ValidationError):
            ActionDrafted(action_id="")


class TestActionApproved:
    def test_reference_trace_phase_11_2_shape(self):
        msg = ActionApproved(action_id="act_001")
        assert msg.action_id == "act_001"


class TestActionDispatched:
    def test_reference_trace_phase_11_3_shape(self):
        msg = ActionDispatched(action_id="act_001")
        assert msg.action_id == "act_001"


class TestActionConfirmed:
    def test_reference_trace_phase_11_4_shape(self):
        msg = ActionConfirmed(action_id="act_001")
        assert msg.action_id == "act_001"


class TestEventClosed:
    def test_reference_trace_phase_15_shape(self):
        msg = EventClosed(event_id="evt_7731")
        assert msg.event_id == "evt_7731"

    def test_rejects_missing_event_id(self):
        with pytest.raises(ValidationError):
            EventClosed()


class TestEventSchemasSerializeRoundTrip:
    @pytest.mark.parametrize(
        "instance",
        [
            TriggerDetected(
                trigger_id="trg_1", project_id="proj_1", occurred_at=datetime.now(timezone.utc)
            ),
            KeysResolved(trigger_id="trg_1"),
            EventCreated(project_id="proj_1", event_id="evt_1", severity=1),
            ImpactTiered(impact_id="imp_1", tier="POSSIBLE", severity=4),
            SeverityComputed(event_id="evt_1", severity=1),
            ActionDrafted(action_id="act_1"),
            ActionApproved(action_id="act_1"),
            ActionDispatched(action_id="act_1"),
            ActionConfirmed(action_id="act_1"),
            EventClosed(event_id="evt_1"),
        ],
    )
    def test_round_trips_through_json(self, instance):
        cls = type(instance)
        restored = cls.model_validate_json(instance.model_dump_json())
        assert restored == instance
