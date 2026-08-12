"""Phase C — table reconstruction and EquipmentRow construction for the
E0.4 New Unit block vertical slice. Consumes dip.tablegrid + dip.ocr;
produces dip.diff.models.EquipmentRow. No RES, no Downstream, no Kafka, no
Neo4j — output stays inside DIP (decision 18)."""

from dip.extract.assignment import CellAssignment, assign_words_to_cells
from dip.extract.build import extract_new_unit_rows
from dip.extract.header_scope import HeaderScopeError, NewUnitColumnMap, locate_new_unit_columns
from dip.extract.normalize import check_mca_fla_suspicious, check_tag_pattern, normalize_numeric

__all__ = [
    "CellAssignment",
    "assign_words_to_cells",
    "extract_new_unit_rows",
    "HeaderScopeError",
    "NewUnitColumnMap",
    "locate_new_unit_columns",
    "check_mca_fla_suspicious",
    "check_tag_pattern",
    "normalize_numeric",
]
