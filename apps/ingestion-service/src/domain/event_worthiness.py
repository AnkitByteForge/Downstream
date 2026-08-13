"""Event-worthiness filter — docs/03 Stage 2: 'decides whether an
EngineeringEventEnvelope is even event-worthy (a drawing revision that only
fixes a typo should never become a Commercial Event; a lightweight, fast,
rule-based filter runs here so the expensive reasoning pipeline in Stage 6
is never wasted on noise)'. docs/05 Phase 2.2: 'does this envelope carry
spec/drawing references at all?'"""

from __future__ import annotations

from envelope_schemas import EngineeringEventEnvelope


def is_event_worthy(envelope: EngineeringEventEnvelope) -> bool:
    return bool(envelope.spec_section_refs or envelope.drawing_refs or envelope.location_refs)
