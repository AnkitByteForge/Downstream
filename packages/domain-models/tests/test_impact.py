import pytest
from pydantic import ValidationError

from domain_models import Impact


def _base_kwargs(**overrides):
    kwargs = dict(
        impact_id="imp_002",
        event_id="evt_7731",
        artifact_ref="po_4471",
        confidence_tier="CERTAIN",
        confidence_reason="RFI-214 §2 cites Spec 23 31 13, exact match to PO-4471's cost code 23-100",
        lifecycle_position_at_detection="IN_FABRICATION",
        evidence_refs=["ev_001"],
        action_id="act_002",
        severity=2,
        status="OPEN",
    )
    kwargs.update(overrides)
    return kwargs


class TestImpactHappyPath:
    def test_reference_trace_imp_002_shape(self):
        impact = Impact(**_base_kwargs())
        assert impact.impact_id == "imp_002"
        assert impact.confidence_tier == "CERTAIN"
        assert impact.severity == 2
        assert impact.status == "OPEN"

    @pytest.mark.parametrize("tier", ["CERTAIN", "PROBABLE", "POSSIBLE"])
    def test_accepts_all_three_confidence_tiers(self, tier):
        impact = Impact(**_base_kwargs(confidence_tier=tier))
        assert impact.confidence_tier == tier

    @pytest.mark.parametrize("status", ["OPEN", "CONTAINED"])
    def test_accepts_both_impact_statuses(self, status):
        impact = Impact(**_base_kwargs(status=status))
        assert impact.status == status

    def test_status_defaults_to_open(self):
        kwargs = _base_kwargs()
        del kwargs["status"]
        impact = Impact(**kwargs)
        assert impact.status == "OPEN"

    def test_evidence_refs_and_action_id_are_optional(self):
        kwargs = _base_kwargs()
        del kwargs["evidence_refs"]
        del kwargs["action_id"]
        impact = Impact(**kwargs)
        assert impact.evidence_refs == []
        assert impact.action_id is None

    def test_serializes_to_json_and_back(self):
        impact = Impact(**_base_kwargs())
        restored = Impact.model_validate_json(impact.model_dump_json())
        assert restored == impact


class TestImpactSeverityBounds:
    def test_rejects_severity_below_one(self):
        with pytest.raises(ValidationError):
            Impact(**_base_kwargs(severity=0))

    def test_rejects_severity_above_four(self):
        with pytest.raises(ValidationError):
            Impact(**_base_kwargs(severity=5))


class TestImpactValidation:
    def test_rejects_invalid_confidence_tier(self):
        with pytest.raises(ValidationError):
            Impact(**_base_kwargs(confidence_tier="LIKELY"))

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            Impact(**_base_kwargs(status="TRIAGED"))

    def test_rejects_empty_confidence_reason(self):
        with pytest.raises(ValidationError):
            Impact(**_base_kwargs(confidence_reason=""))

    def test_rejects_missing_artifact_ref(self):
        kwargs = _base_kwargs()
        del kwargs["artifact_ref"]
        with pytest.raises(ValidationError):
            Impact(**kwargs)

    def test_is_frozen(self):
        impact = Impact(**_base_kwargs())
        with pytest.raises(ValidationError):
            impact.status = "CONTAINED"
