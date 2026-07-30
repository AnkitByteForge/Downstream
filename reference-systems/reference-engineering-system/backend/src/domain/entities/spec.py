from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpecDivision:
    """CSI MasterFormat division, e.g. number="23", title="Heating, Ventilating,
    and Air Conditioning (HVAC)"."""

    number: str
    title: str


@dataclass
class SpecSection:
    """CSI MasterFormat section, e.g. number="23 31 13" (Reference Engineering
    System doc §6)."""

    id: int | None
    project_id: int
    division_number: str
    number: str
    title: str
    substitution_policy: str | None = None
