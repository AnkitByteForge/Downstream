from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Discipline:
    """US National CAD Standard discipline designator (Reference Engineering
    System doc §13), e.g. code="M", name="Mechanical"."""

    code: str
    name: str


@dataclass
class Project:
    id: int | None
    name: str
    spec_format: str  # "MF2020" | "MF16"
