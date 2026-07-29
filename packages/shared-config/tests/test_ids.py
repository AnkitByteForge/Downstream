import pytest

from shared_config import ID_PREFIXES, generate_id, is_valid_id


class TestIdPrefixes:
    def test_matches_reference_trace_prefixes_exactly(self):
        assert ID_PREFIXES == {
            "trigger": "trg",
            "commercial_event": "evt",
            "impact": "imp",
            "action": "act",
            "approval": "apr",
        }


class TestGenerateId:
    @pytest.mark.parametrize(
        "entity,prefix",
        [
            ("trigger", "trg"),
            ("commercial_event", "evt"),
            ("impact", "imp"),
            ("action", "act"),
            ("approval", "apr"),
        ],
    )
    def test_generates_id_with_correct_prefix(self, entity, prefix):
        generated = generate_id(entity)
        assert generated.startswith(f"{prefix}_")

    def test_generated_ids_are_unique(self):
        ids = {generate_id("commercial_event") for _ in range(200)}
        assert len(ids) == 200

    def test_respects_suffix_length(self):
        generated = generate_id("action", suffix_length=12)
        suffix = generated.removeprefix("act_")
        assert len(suffix) == 12

    def test_rejects_unknown_entity(self):
        with pytest.raises(ValueError):
            generate_id("vendor")  # type: ignore[arg-type]

    def test_rejects_non_positive_suffix_length(self):
        with pytest.raises(ValueError):
            generate_id("trigger", suffix_length=0)


class TestIsValidId:
    def test_accepts_well_formed_ids_from_the_reference_trace(self):
        assert is_valid_id("trigger", "trg_2f9a1c")
        assert is_valid_id("commercial_event", "evt_7731")
        assert is_valid_id("impact", "imp_001")
        assert is_valid_id("action", "act_001")
        assert is_valid_id("approval", "apr_001")

    def test_rejects_wrong_prefix(self):
        assert not is_valid_id("trigger", "evt_7731")

    def test_rejects_prefix_with_no_suffix(self):
        assert not is_valid_id("trigger", "trg_")
        assert not is_valid_id("trigger", "trg")

    def test_rejects_empty_string(self):
        assert not is_valid_id("commercial_event", "")

    def test_round_trips_with_generate_id(self):
        for entity in ID_PREFIXES:
            assert is_valid_id(entity, generate_id(entity))

    def test_rejects_unknown_entity(self):
        with pytest.raises(ValueError):
            is_valid_id("vendor", "vnd_1")  # type: ignore[arg-type]
