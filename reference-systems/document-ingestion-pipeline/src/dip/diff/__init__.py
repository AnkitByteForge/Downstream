"""Phase D — deterministic revision diff, independent of OCR/Phase C.

Also fixes Phase C's future contract: EquipmentRow is the first extraction
target only, not a frozen universal ingestion model (see models.py). A
future structured document type (a panel schedule, a one-line-diagram
equipment list) gets its own Pydantic model; diff_schedule() only requires
that the model expose the fields named in its `key` and `compare_fields`
arguments — it is not hardcoded to EquipmentRow's own field names.
"""

from dip.diff.engine import diff_schedule
from dip.diff.models import DetectedChange, EquipmentRow, FieldChange, RowChange

__all__ = ["diff_schedule", "DetectedChange", "EquipmentRow", "FieldChange", "RowChange"]
