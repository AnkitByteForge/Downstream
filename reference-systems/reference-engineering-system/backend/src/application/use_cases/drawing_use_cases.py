from __future__ import annotations

from dataclasses import replace

from application.exceptions import NotFound
from application.ports import ClockPort, WebhookDispatcherPort
from application.webhook_payloads import build_thin_payload
from domain.entities import Drawing, DrawingVersion, WebhookDelivery
from domain.repositories import (
    DrawingRepository,
    DrawingVersionRepository,
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)
from domain.state_machines import drawing_version_transitions
from domain.value_objects import RevisionCloud


class CreateDrawing:
    """ADR-009/E.4: idempotent creation. (project_id, sheet_number) is a
    Drawing's natural key -- a repeated call with the same key returns the
    existing row (created=False) rather than inserting a duplicate. This
    check-then-insert path is what makes a SEQUENTIAL retry (create,
    network failure before the caller sees the response, retry) a
    guaranteed no-op, which is the exact scenario the promotion
    orchestrator (E.6) needs. Migration 0015's DB-level UNIQUE constraint
    is the hard backstop: it is what the domain actually depends on for
    the invariant "no duplicate Drawing for this (project, sheet_number)"
    to hold even under a genuine concurrent race between two simultaneous
    callers -- a scenario this use case does not itself additionally
    detect-and-recover from, since DIP's promotion orchestrator is a
    serial process with no concurrent writers by construction (a
    documented scope boundary, not an oversight). A real race would
    surface as a database constraint error rather than silently creating
    two rows.
    """

    def __init__(self, drawing_repo: DrawingRepository) -> None:
        self._drawing_repo = drawing_repo

    def execute(
        self, project_id: int, sheet_number: str, title: str, discipline_code: str
    ) -> tuple[Drawing, bool]:
        existing = self._drawing_repo.get_by_sheet_number(project_id, sheet_number)
        if existing is not None:
            return existing, False
        created = self._drawing_repo.add(
            Drawing(
                id=None,
                project_id=project_id,
                sheet_number=sheet_number,
                title=title,
                discipline_code=discipline_code,
                current_version_id=None,
            )
        )
        return created, True


class CreateDrawingVersion:
    """ADR-009/E.4: idempotent creation, same posture as CreateDrawing but
    keyed on (drawing_id, revision_label). Always creates in DRAFT status
    -- issuance remains the existing, unmodified IssueDrawingVersion use
    case (RES-4B); this use case never issues a version and never
    dispatches a webhook. issuance_date is stamped with the current time
    as a placeholder (mirroring every DRAFT DrawingVersion the seed script
    already creates this way) -- it carries no meaning until
    IssueDrawingVersion overwrites it at actual issuance.
    """

    def __init__(
        self,
        drawing_repo: DrawingRepository,
        version_repo: DrawingVersionRepository,
        clock: ClockPort,
    ) -> None:
        self._drawing_repo = drawing_repo
        self._version_repo = version_repo
        self._clock = clock

    def execute(
        self,
        drawing_id: int,
        revision_label: str,
        discipline_code: str,
        revision_clouds: list[RevisionCloud] | None = None,
    ) -> tuple[DrawingVersion, bool]:
        drawing = self._drawing_repo.get(drawing_id)
        if drawing is None:
            raise NotFound("Drawing", drawing_id)

        existing = self._version_repo.get_by_drawing_and_label(drawing_id, revision_label)
        if existing is not None:
            return existing, False

        created = self._version_repo.add(
            DrawingVersion(
                id=None,
                drawing_id=drawing_id,
                revision_label=revision_label,
                issuance_date=self._clock.now().date(),
                status="DRAFT",
                discipline_code=discipline_code,
                revision_clouds=list(revision_clouds or []),
            )
        )
        return created, True


class ListDrawings:
    def __init__(self, drawing_repo: DrawingRepository) -> None:
        self._drawing_repo = drawing_repo

    def execute(self, project_id: int) -> list[Drawing]:
        return self._drawing_repo.list_by_project(project_id)


class GetDrawing:
    def __init__(self, drawing_repo: DrawingRepository) -> None:
        self._drawing_repo = drawing_repo

    def execute(self, drawing_id: int) -> Drawing:
        drawing = self._drawing_repo.get(drawing_id)
        if drawing is None:
            raise NotFound("Drawing", drawing_id)
        return drawing


class ListDrawingVersions:
    """Backs the Drawing Revision Timeline ? every version of a sheet, in
    issuance order, so the supersession chain is fully visible."""

    def __init__(self, version_repo: DrawingVersionRepository) -> None:
        self._version_repo = version_repo

    def execute(self, drawing_id: int) -> list[DrawingVersion]:
        versions = self._version_repo.list_by_drawing(drawing_id)
        return sorted(versions, key=lambda v: v.issuance_date)


class GetDrawingVersion:
    def __init__(self, version_repo: DrawingVersionRepository) -> None:
        self._version_repo = version_repo

    def execute(self, version_id: int) -> DrawingVersion:
        version = self._version_repo.get(version_id)
        if version is None:
            raise NotFound("DrawingVersion", version_id)
        return version


class IssueDrawingVersion:
    """Closes the RES-4 DrawingVersion issuance gap (IMPLEMENTATION_STATUS ?13).

    Loads the version, applies the existing legal DrawingVersion issuance
    transition (DRAFT -> ISSUED), stamps the issuance date, supersedes the
    prior current version of the same sheet, repoints the Drawing at the newly
    issued version, and emits the thin documents/update webhook
    (resource_id = the issued version id). The transition's save/update calls
    share one per-request session (see deps.get_db_session), so the issuance,
    supersession and drawing repoint commit atomically at the request boundary.
    """

    def __init__(
        self,
        drawing_repo: DrawingRepository,
        version_repo: DrawingVersionRepository,
        clock: ClockPort,
        webhook_subscription_repo: WebhookSubscriptionRepository,
        webhook_delivery_repo: WebhookDeliveryRepository,
        webhook_dispatcher: WebhookDispatcherPort,
    ) -> None:
        self._drawing_repo = drawing_repo
        self._version_repo = version_repo
        self._clock = clock
        self._webhook_subscription_repo = webhook_subscription_repo
        self._webhook_delivery_repo = webhook_delivery_repo
        self._webhook_dispatcher = webhook_dispatcher

    def execute(self, version_id: int) -> DrawingVersion:
        version = self._version_repo.get(version_id)
        if version is None:
            raise NotFound("DrawingVersion", version_id)
        drawing = self._drawing_repo.get(version.drawing_id)
        if drawing is None:
            raise NotFound("Drawing", version.drawing_id)

        issued = drawing_version_transitions.issue_version(version)
        issued = replace(issued, issuance_date=self._clock.now().date())

        prior_id = drawing.current_version_id
        if prior_id is not None and prior_id != version_id:
            prior = self._version_repo.get(prior_id)
            if prior is not None and prior.status != "SUPERSEDED":
                superseded = drawing_version_transitions.supersede(prior, superseded_by_id=version_id)
                self._version_repo.update(superseded)

        saved = self._version_repo.update(issued)
        self._drawing_repo.update(replace(drawing, current_version_id=version_id))
        self._dispatch_webhooks(drawing, saved)
        return saved

    def _dispatch_webhooks(self, drawing: Drawing, version: DrawingVersion) -> None:
        occurred_at = self._clock.now()
        subscriptions = self._webhook_subscription_repo.list_matching(
            drawing.project_id, "documents", "update"
        )
        for subscription in subscriptions:
            payload = build_thin_payload(
                "documents", version.id, drawing.project_id, "update", occurred_at
            )
            delivered = self._webhook_dispatcher.dispatch(subscription, payload)
            self._webhook_delivery_repo.add(
                WebhookDelivery(
                    id=None,
                    project_id=drawing.project_id,
                    subscription_id=subscription.id,
                    resource_name="documents",
                    resource_id=version.id,
                    event_type="update",
                    occurred_at=occurred_at,
                    status="SENT" if delivered else "FAILED",
                    dispatched_at=self._clock.now(),
                )
            )
