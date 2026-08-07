from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from domain.value_objects import BallInCourt


@dataclass
class SubmittalPackage:
    """A grouping of related submittals reviewed as one cycle (ADR-005).
    RES-3's own seed data instantiates none — a submittal's package_id may
    be None."""

    id: int | None
    project_id: int
    name: str
    description: str | None = None


@dataclass
class SubmittalReviewStatus:
    """One row of the project's own configurable disposition vocabulary
    (ADR-003). gates_procurement is the single field the entire procurement
    gate mechanism hinges on; is_terminal governs whether a revision may
    still receive a new disposition."""

    id: int | None
    project_id: int
    code: str
    label: str
    gates_procurement: bool
    is_terminal: bool
    sort_order: int = 0


@dataclass
class SubmittalRequirement:
    """A spec-driven submittal register entry — what a SpecSection requires,
    independent of whether any submittal has been made against it yet."""

    id: int | None
    project_id: int
    spec_section_id: int
    submittal_type: str  # shop_drawing | product_data | sample
    category: str  # action | informational


@dataclass
class Submittal:
    """Envelope-level fields only — everything that changes per revision
    lives on SubmittalRevision (ADR-004)."""

    id: int | None
    project_id: int
    number: str
    spec_section_id: int
    package_id: int | None = None
    vendor_id: int | None = None
    commitment_id: int | None = None
    submittal_type: str = "shop_drawing"
    category: str = "action"
    lead_time_days: int | None = None
    required_on_site_date: date | None = None


@dataclass
class SubmittalRevision:
    id: int | None
    submittal_id: int
    rev_label: str
    review_status_id: int
    ball_in_court: BallInCourt
    equipment_tag: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    capacity_value: float | None = None
    capacity_unit: str | None = None
    # MCA and FLA are explicit, nullable, first-class engineering fields on the
    # revision (ADR-006). Kept as a scalar pair mirroring capacity_value/unit —
    # deliberately NOT a generic electrical-properties framework, because the
    # canonical Scenario B demo (SUB-118 Rev 0 -> Rev 1) diffs exactly these
    # two values (180A/150A -> 240A/200A) across revisions. Nullable so
    # non-electrical submittals or revisions where FLA is unknown remain valid.
    fla_value: float | None = None
    fla_unit: str | None = None
    submitted_at: datetime | None = None
    disposed_by_user_id: int | None = None
    disposition_at: datetime | None = None
    drawing_version_ids: list[int] = field(default_factory=list)
    location_ids: list[int] = field(default_factory=list)
