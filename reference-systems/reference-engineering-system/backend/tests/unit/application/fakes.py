from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from application.ports import ClockPort, WebhookDispatcherPort
from domain.entities import RFI, WebhookDelivery, WebhookSubscription
from domain.entities.submittal import Submittal, SubmittalReviewStatus, SubmittalRevision
from domain.repositories import RFIRepository, WebhookDeliveryRepository, WebhookSubscriptionRepository
from domain.repositories.submittal_repository import (
    SubmittalRepository,
    SubmittalReviewStatusRepository,
    SubmittalRevisionRepository,
)


class FakeClock(ClockPort):
    def __init__(self, fixed: datetime | None = None) -> None:
        self._fixed = fixed or datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._fixed


class InMemoryRFIRepository(RFIRepository):
    """Proves a use case is fully testable with zero database — the whole
    point of the repository-port split in Clean Architecture."""

    def __init__(self) -> None:
        self._rows: dict[int, RFI] = {}
        self._next_id = 1

    def get(self, rfi_id: int) -> RFI | None:
        return self._rows.get(rfi_id)

    def list_by_project(self, project_id: int) -> list[RFI]:
        return [r for r in self._rows.values() if r.project_id == project_id]

    def add(self, rfi: RFI) -> RFI:
        rfi = replace(rfi, id=self._next_id)
        self._rows[rfi.id] = rfi
        self._next_id += 1
        return rfi

    def update(self, rfi: RFI) -> RFI:
        self._rows[rfi.id] = rfi
        return rfi


class InMemoryWebhookSubscriptionRepository(WebhookSubscriptionRepository):
    def __init__(self, seeded: list[WebhookSubscription] | None = None) -> None:
        self._rows: list[WebhookSubscription] = list(seeded or [])
        self._next_id = 1

    def add(self, subscription: WebhookSubscription) -> WebhookSubscription:
        subscription = replace(subscription, id=self._next_id)
        self._next_id += 1
        self._rows.append(subscription)
        return subscription

    def list_by_project(self, project_id: int) -> list[WebhookSubscription]:
        return [s for s in self._rows if s.project_id == project_id]

    def list_matching(
        self, project_id: int, resource_name: str, event_type: str
    ) -> list[WebhookSubscription]:
        return [
            s
            for s in self._rows
            if s.project_id == project_id
            and s.resource_name == resource_name
            and s.event_type == event_type
        ]


class InMemoryWebhookDeliveryRepository(WebhookDeliveryRepository):
    def __init__(self) -> None:
        self.rows: list[WebhookDelivery] = []
        self._next_id = 1

    def add(self, delivery: WebhookDelivery) -> WebhookDelivery:
        delivery = replace(delivery, id=self._next_id)
        self._next_id += 1
        self.rows.append(delivery)
        return delivery

    def list_by_project(self, project_id: int, limit: int) -> list[WebhookDelivery]:
        return [d for d in self.rows if d.project_id == project_id][:limit]


class InMemorySubmittalRepository(SubmittalRepository):
    def __init__(self, seeded: list[Submittal] | None = None) -> None:
        self._rows: dict[int, Submittal] = {s.id: s for s in (seeded or [])}
        self._next_id = max(self._rows, default=0) + 1

    def add(self, submittal: Submittal) -> Submittal:
        submittal = replace(submittal, id=self._next_id)
        self._rows[submittal.id] = submittal
        self._next_id += 1
        return submittal

    def get(self, submittal_id: int) -> Submittal | None:
        return self._rows.get(submittal_id)

    def list_by_project(self, project_id: int) -> list[Submittal]:
        return [s for s in self._rows.values() if s.project_id == project_id]


class InMemorySubmittalRevisionRepository(SubmittalRevisionRepository):
    def __init__(self, seeded: list[SubmittalRevision] | None = None) -> None:
        self._rows: dict[int, SubmittalRevision] = {r.id: r for r in (seeded or [])}
        self._next_id = max(self._rows, default=0) + 1

    def add(self, revision: SubmittalRevision) -> SubmittalRevision:
        revision = replace(revision, id=self._next_id)
        self._rows[revision.id] = revision
        self._next_id += 1
        return revision

    def update(self, revision: SubmittalRevision) -> SubmittalRevision:
        self._rows[revision.id] = revision
        return revision

    def get(self, revision_id: int) -> SubmittalRevision | None:
        return self._rows.get(revision_id)

    def list_by_submittal(self, submittal_id: int) -> list[SubmittalRevision]:
        return [r for r in self._rows.values() if r.submittal_id == submittal_id]


class InMemorySubmittalReviewStatusRepository(SubmittalReviewStatusRepository):
    def __init__(self, seeded: list[SubmittalReviewStatus] | None = None) -> None:
        self._rows: dict[int, SubmittalReviewStatus] = {s.id: s for s in (seeded or [])}

    def add(self, status: SubmittalReviewStatus) -> SubmittalReviewStatus:
        self._rows[status.id] = status
        return status

    def get(self, status_id: int) -> SubmittalReviewStatus | None:
        return self._rows.get(status_id)

    def get_by_code(self, project_id: int, code: str) -> SubmittalReviewStatus | None:
        for s in self._rows.values():
            if s.project_id == project_id and s.code == code:
                return s
        return None

    def list_by_project(self, project_id: int) -> list[SubmittalReviewStatus]:
        return [s for s in self._rows.values() if s.project_id == project_id]


class FakeWebhookDispatcher(WebhookDispatcherPort):
    """Records every payload it was asked to send instead of making a real
    HTTP call — lets a test assert the exact shape dispatched, per docs/04's
    "the thin payload is the most important thing to get right"."""

    def __init__(self, always_succeed: bool = True) -> None:
        self.always_succeed = always_succeed
        self.calls: list[tuple[WebhookSubscription, dict]] = []

    def dispatch(self, subscription: WebhookSubscription, payload: dict) -> bool:
        self.calls.append((subscription, payload))
        return self.always_succeed
