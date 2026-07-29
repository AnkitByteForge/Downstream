from event_contracts import ALL_TOPICS, PARTITION_KEY_FIELD, TOPIC_SCHEMAS
from event_contracts.topics import (
    ACTION_APPROVED,
    ACTION_CONFIRMED,
    ACTION_DISPATCHED,
    ACTION_DRAFTED,
    EVENT_CLOSED,
    EVENT_CREATED,
    IMPACT_TIERED,
    KEYS_RESOLVED,
    SEVERITY_COMPUTED,
    TRIGGER_DETECTED,
)


class TestTopicList:
    def test_exactly_ten_topics(self):
        """docs/07_Downstream_Implementation_Blueprint.md §8: 'All ten are
        the complete topic list this scope requires.'"""
        assert len(ALL_TOPICS) == 10

    def test_topic_names_match_blueprint_exactly(self):
        assert set(ALL_TOPICS) == {
            "trigger.detected",
            "keys.resolved",
            "event.created",
            "impact.tiered",
            "severity.computed",
            "action.drafted",
            "action.approved",
            "action.dispatched",
            "action.confirmed",
            "event.closed",
        }

    def test_graph_updated_is_deliberately_absent(self):
        """docs/03 §3 names an eleventh topic, graph.updated; docs/07 §8
        deliberately scopes it out of this milestone. See topics.py docstring."""
        assert "graph.updated" not in ALL_TOPICS

    def test_partition_key_field_is_project_id(self):
        assert PARTITION_KEY_FIELD == "project_id"

    def test_topic_schemas_covers_every_topic(self):
        assert set(TOPIC_SCHEMAS.keys()) == set(ALL_TOPICS)

    def test_every_topic_constant_is_registered_in_topic_schemas(self):
        for topic in (
            TRIGGER_DETECTED,
            KEYS_RESOLVED,
            EVENT_CREATED,
            IMPACT_TIERED,
            SEVERITY_COMPUTED,
            ACTION_DRAFTED,
            ACTION_APPROVED,
            ACTION_DISPATCHED,
            ACTION_CONFIRMED,
            EVENT_CLOSED,
        ):
            assert topic in TOPIC_SCHEMAS
