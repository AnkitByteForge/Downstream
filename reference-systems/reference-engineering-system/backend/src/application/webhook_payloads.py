from __future__ import annotations

from datetime import datetime


def build_thin_payload(
    resource_name: str, resource_id: int, project_id: int, event_type: str, timestamp: datetime
) -> dict:
    """The exact five-field thin shape from Reference Execution Trace Phase 0
    — resource_name, resource_id, project_id, event_type, timestamp, nothing
    else. This is the single most important shape in the whole system to get
    right (docs/04): a subscriber must be forced to GET back for detail, the
    same way real Procore's webhooks work. A contract test asserts this
    function's output key set never grows.
    """
    return {
        "resource_name": resource_name,
        "resource_id": resource_id,
        "project_id": project_id,
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
    }
