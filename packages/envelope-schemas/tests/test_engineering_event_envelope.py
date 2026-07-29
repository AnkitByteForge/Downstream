from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from envelope_schemas import DrawingRef, EngineeringEventEnvelope


def _base_kwargs(**overrides):
    kwargs = dict(
        source_system="procore",
        source_id="4821356",
        display_number="RFI-214",
        type="RFI_APPROVED",
        spec_section_refs=["23 31 13"],
        drawing_refs=[DrawingRef(item_id="doc_M-2.1", version_id="rev_C")],
        location_refs=["Level 4, Grid B-4"],
        raw_document_ref="procore://attachments/991211",
        region="us-east",
        acting_credential_scope="partial:[rfis,submittals,documents]",
        occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
    )
    kwargs.update(overrides)
    return kwargs


class TestEngineeringEventEnvelopeHappyPath:
    def test_reference_trace_phase_1_3_shape_round_trips(self):
        """The exact envelope shown in Phase 1.3 of the Reference Execution
        Trace must validate and serialize back out unchanged."""
        envelope = EngineeringEventEnvelope(**_base_kwargs())

        assert envelope.envelope_type == "EngineeringEventEnvelope"
        assert envelope.source_system == "procore"
        assert envelope.source_id == "4821356"
        assert envelope.display_number == "RFI-214"
        assert envelope.type == "RFI_APPROVED"
        assert envelope.spec_section_refs == ["23 31 13"]
        assert envelope.drawing_refs == [DrawingRef(item_id="doc_M-2.1", version_id="rev_C")]
        assert envelope.location_refs == ["Level 4, Grid B-4"]
        assert envelope.raw_document_ref == "procore://attachments/991211"
        assert envelope.region == "us-east"
        assert envelope.acting_credential_scope == "partial:[rfis,submittals,documents]"

    def test_serializes_to_json_and_back(self):
        envelope = EngineeringEventEnvelope(**_base_kwargs())
        restored = EngineeringEventEnvelope.model_validate_json(envelope.model_dump_json())
        assert restored == envelope

    @pytest.mark.parametrize("event_type", ["RFI_APPROVED", "DRAWING_REVISED", "SPEC_UPDATED"])
    def test_accepts_all_three_canonical_event_types(self, event_type):
        envelope = EngineeringEventEnvelope(**_base_kwargs(type=event_type))
        assert envelope.type == event_type

    def test_envelope_type_defaults_without_being_supplied(self):
        envelope = EngineeringEventEnvelope(**_base_kwargs())
        assert envelope.envelope_type == "EngineeringEventEnvelope"

    def test_optional_fields_default_to_empty_or_none(self):
        envelope = EngineeringEventEnvelope(
            source_system="procore",
            source_id="1",
            type="SPEC_UPDATED",
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        assert envelope.display_number is None
        assert envelope.spec_section_refs == []
        assert envelope.drawing_refs == []
        assert envelope.location_refs == []
        assert envelope.raw_document_ref is None
        assert envelope.region is None
        assert envelope.acting_credential_scope is None


class TestEngineeringEventEnvelopeValidation:
    def test_rejects_invalid_event_type(self):
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**_base_kwargs(type="TYPO_FIX"))

    def test_rejects_missing_source_system(self):
        kwargs = _base_kwargs()
        del kwargs["source_system"]
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**kwargs)

    def test_rejects_empty_source_system(self):
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**_base_kwargs(source_system=""))

    def test_rejects_missing_source_id(self):
        kwargs = _base_kwargs()
        del kwargs["source_id"]
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**kwargs)

    def test_rejects_missing_occurred_at(self):
        kwargs = _base_kwargs()
        del kwargs["occurred_at"]
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**kwargs)

    def test_rejects_wrong_envelope_type_literal(self):
        with pytest.raises(ValidationError):
            EngineeringEventEnvelope(**_base_kwargs(envelope_type="CommercialArtifactSnapshot"))

    def test_envelope_is_frozen(self):
        envelope = EngineeringEventEnvelope(**_base_kwargs())
        with pytest.raises(ValidationError):
            envelope.source_id = "different"


class TestDrawingRef:
    def test_keeps_item_id_and_version_id_distinct(self):
        ref = DrawingRef(item_id="doc_M-2.1", version_id="rev_C")
        assert ref.item_id == "doc_M-2.1"
        assert ref.version_id == "rev_C"

    def test_rejects_empty_item_id(self):
        with pytest.raises(ValidationError):
            DrawingRef(item_id="", version_id="rev_C")

    def test_rejects_empty_version_id(self):
        with pytest.raises(ValidationError):
            DrawingRef(item_id="doc_M-2.1", version_id="")

    def test_rejects_missing_version_id(self):
        with pytest.raises(ValidationError):
            DrawingRef(item_id="doc_M-2.1")

    def test_is_frozen(self):
        ref = DrawingRef(item_id="doc_M-2.1", version_id="rev_C")
        with pytest.raises(ValidationError):
            ref.version_id = "rev_D"
