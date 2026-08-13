"""Pure-logic unit test — no database. docs/03 Stage 2 / docs/05 Phase 2.2:
'does this envelope carry spec/drawing references at all?'"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from envelope_schemas import DrawingRef, EngineeringEventEnvelope

from domain.event_worthiness import is_event_worthy

OCCURRED_AT = datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)


def _envelope(**overrides) -> EngineeringEventEnvelope:
    defaults = dict(
        source_system="procore",
        source_id="4821356",
        type="RFI_APPROVED",
        occurred_at=OCCURRED_AT,
    )
    defaults.update(overrides)
    return EngineeringEventEnvelope(**defaults)


def test_worthy_with_spec_section_ref():
    envelope = _envelope(spec_section_refs=["23 31 13"])
    assert is_event_worthy(envelope) is True


def test_worthy_with_drawing_ref():
    envelope = _envelope(drawing_refs=[DrawingRef(item_id="M-2.1", version_id="Rev C")])
    assert is_event_worthy(envelope) is True


def test_worthy_with_location_ref():
    envelope = _envelope(location_refs=["Grid B-4"])
    assert is_event_worthy(envelope) is True


def test_not_worthy_with_no_refs_at_all():
    """The typo-fix-revision case docs/03/05 both name: no spec, drawing, or
    location reference at all — never reaches full reasoning."""
    envelope = _envelope()
    assert is_event_worthy(envelope) is False
