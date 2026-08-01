from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Vendor:
    id: int | None
    project_id: int
    name: str


@dataclass
class Commitment:
    """RES-3's own minimal Commitment — deliberately lifecycle-free (no
    fabrication/shipped status). The rich, lifecycle-bearing PO records the
    Enterprise Fidelity Review's HVAC scenario describes belong entirely to
    the not-yet-built Reference Commercial System; this entity is only the
    lightweight pointer a real Procore-shaped system natively holds
    (docs/04: "a single Procore connection can... satisfy both Engineering
    and Commercial connector families")."""

    id: int | None
    project_id: int
    vendor_id: int
    cost_code: str
    description: str
    amount: float
    spec_section_id: int | None = None
