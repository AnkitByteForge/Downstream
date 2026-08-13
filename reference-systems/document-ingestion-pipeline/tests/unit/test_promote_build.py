"""E.6 -- the promotion orchestrator. Tested entirely against a fake RES
client (duck-typed to ResPromotionClient's create_drawing/
create_drawing_version signatures) and a fake sleep function -- no real
network, no real RES instance, no real time spent sleeping during retries."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dip.diff.models import EquipmentRow
from dip.promote.build import (
    PromotionAttemptRecord,
    evidence_ref_uri,
    promote_snapshot,
    promotion_log_path,
)
from dip.promote.models import StructuredStateSnapshot
from dip.promote.res_client import ResClientError, ResHttpError
from dip.provenance import EvidenceRef


@pytest.fixture(autouse=True)
def isolated_promotion_log_dir(tmp_path, monkeypatch):
    from dip import config

    monkeypatch.setattr(config, "PROMOTION_LOG_DIR", tmp_path / "promotion_log")
    yield


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extraction_method="raster_ocr",
        extractor_version="dip-extract-0.1.0",
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ocr_engine="tesseract",
    )


def _row(tag: str, breaker_status: str = "VALID", breaker_rating: str = "60/3") -> EquipmentRow:
    return EquipmentRow(
        tag=tag,
        existing_designation="(E) AH-3",
        fed_from_panel="MR4",
        breaker_rating=breaker_rating,
        conduit="1 in",
        volts="480",
        fla="56.0",
        mca="58.0",
        fla_numeric=56.0,
        mca_numeric=58.0,
        evidence=_evidence(),
        field_validation={
            "fed_from_panel": "VALID",
            "breaker_rating": breaker_status,
            "conduit": "VALID",
            "volts": "VALID",
            "fla": "VALID",
            "mca": "VALID",
        },
    )


def _snapshot(rows) -> StructuredStateSnapshot:
    return StructuredStateSnapshot(
        document_id="fake_doc_id",
        file_name="fake.pdf",
        page_index=373,
        page_label="E0.4",
        extractor_version="dip-extract-0.1.0",
        ocr_engine="tesseract",
        render_scale=2.0,
        extracted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        rows=rows,
    )


class FakeResClient:
    """Duck-typed to ResPromotionClient's public surface. Each of
    create_drawing/create_drawing_version can be scripted to raise N times
    (from a queue of exceptions) before succeeding, so retry behavior is
    testable without a real network."""

    def __init__(self) -> None:
        self.create_drawing_calls: list[dict] = []
        self.create_drawing_version_calls: list[dict] = []
        self._drawing_id_seq = 100
        self._version_id_seq = 900
        self._drawings: dict[tuple[int, str], dict] = {}
        self._versions: dict[tuple[int, str], dict] = {}
        self.create_drawing_raises: list[Exception] = []
        self.create_drawing_version_raises: list[Exception] = []

    def create_drawing(self, project_id, sheet_number, title, discipline_code):
        self.create_drawing_calls.append(
            {"project_id": project_id, "sheet_number": sheet_number, "title": title, "discipline_code": discipline_code}
        )
        if self.create_drawing_raises:
            raise self.create_drawing_raises.pop(0)
        key = (project_id, sheet_number)
        if key not in self._drawings:
            self._drawing_id_seq += 1
            self._drawings[key] = {"id": self._drawing_id_seq, "sheet_number": sheet_number}
        return self._drawings[key]

    def create_drawing_version(self, project_id, drawing_id, revision_label, discipline_code, revision_clouds=None):
        self.create_drawing_version_calls.append(
            {
                "project_id": project_id,
                "drawing_id": drawing_id,
                "revision_label": revision_label,
                "discipline_code": discipline_code,
                "revision_clouds": revision_clouds,
            }
        )
        if self.create_drawing_version_raises:
            raise self.create_drawing_version_raises.pop(0)
        key = (drawing_id, revision_label)
        if key not in self._versions:
            self._version_id_seq += 1
            self._versions[key] = {
                "id": self._version_id_seq,
                "revision_label": revision_label,
                "revision_clouds": revision_clouds,
            }
        return self._versions[key]


def _fake_sleep_recorder():
    delays: list[float] = []
    return delays, delays.append


class TestOnlyValidFactsCrossTheBoundary:
    def test_ambiguous_field_never_appears_in_revision_clouds(self):
        row = _row("AH-9C", breaker_status="AMBIGUOUS", breaker_rating="2513")
        snapshot = _snapshot([row])
        client = FakeResClient()
        delays, sleep = _fake_sleep_recorder()

        result = promote_snapshot(
            snapshot,
            client,
            target_project_id=1,
            sheet_number="E0.4",
            drawing_title="Air Handler Schedule",
            discipline_code="E",
            revision_label="Rev A",
            sleep=sleep,
        )

        descriptions = [c["description"] for c in client.create_drawing_version_calls[0]["revision_clouds"]]
        assert not any("2513" in d for d in descriptions)
        assert not any(d.startswith("breaker_rating") for d in descriptions)
        assert all(f.field_name != "breaker_rating" for f in result.promoted_facts)

    def test_field_with_no_validation_status_never_appears(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        result = promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        assert all(f.field_name != "tag" for f in result.promoted_facts)
        assert all(f.field_name != "existing_designation" for f in result.promoted_facts)

    def test_only_valid_fields_are_sent_to_res(self):
        row = _row("AH-9C")  # all six validated fields are VALID
        snapshot = _snapshot([row])
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        clouds = client.create_drawing_version_calls[0]["revision_clouds"]
        assert len(clouds) == 6  # fed_from_panel, breaker_rating, conduit, volts, fla, mca


class TestDeterministicIdentityAndOrdering:
    def test_revision_clouds_are_sorted_deterministically_by_tag_and_field(self):
        rows = [_row("AH-9C"), _row("AH-2B")]
        snapshot = _snapshot(rows)
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        clouds = client.create_drawing_version_calls[0]["revision_clouds"]
        areas = [c["area"] for c in clouds]
        assert areas == sorted(areas)  # AH-2B's rows sort before AH-9C's
        assert areas[0].endswith("AH-2B")

    def test_source_evidence_ref_matches_the_documented_uri_shape(self):
        assert evidence_ref_uri("deadbeef", 373, "fed_from_panel", "AH-9A") == (
            "dip://document/deadbeef/page/373/field/fed_from_panel?row=AH-9A"
        )

    def test_repeated_promotion_of_the_same_snapshot_sends_byte_identical_revision_clouds(self):
        snapshot = _snapshot([_row("AH-9C"), _row("AH-2B")])
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )
        promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        first_clouds = client.create_drawing_version_calls[0]["revision_clouds"]
        second_clouds = client.create_drawing_version_calls[1]["revision_clouds"]
        assert first_clouds == second_clouds


class TestIdempotentRerun:
    def test_rerunning_promotion_never_creates_a_duplicate_drawing_or_version(self):
        """The exact scenario named in the milestone spec: run #1 succeeds,
        run #2 (a retry/rerun of the same logical promotion) must return
        the SAME drawing_id/drawing_version_id, not new ones."""
        snapshot = _snapshot([_row("AH-9C")])
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        result_1 = promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )
        result_2 = promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        assert result_1.drawing["id"] == result_2.drawing["id"]
        assert result_1.drawing_version["id"] == result_2.drawing_version["id"]
        assert len(client.create_drawing_calls) == 2  # both calls made, RES's own idempotency absorbs it
        assert len({c["id"] for c in [result_1.drawing, result_2.drawing]}) == 1


class TestRetryAndFailureHandling:
    def test_retryable_error_is_retried_and_eventually_succeeds(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        client.create_drawing_raises = [ResHttpError("http://x", 503, {"detail": "unavailable"})]
        delays, sleep = _fake_sleep_recorder()

        result = promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        assert result.attempt.outcome == "SUCCESS"
        assert len(client.create_drawing_calls) == 2  # first failed, second succeeded
        assert delays == [1.0]  # one backoff delay, base_seconds=1.0 * 2**0

    def test_bounded_exponential_backoff_delays(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        client.create_drawing_raises = [
            ResHttpError("http://x", 503, {}),
            ResHttpError("http://x", 503, {}),
        ]
        delays, sleep = _fake_sleep_recorder()

        promote_snapshot(
            snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep, max_attempts=3,
        )

        assert delays == [1.0, 2.0]  # exponential: base * 2**0, base * 2**1

    def test_retries_are_bounded_not_infinite(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        client.create_drawing_raises = [
            ResHttpError("http://x", 503, {}),
            ResHttpError("http://x", 503, {}),
            ResHttpError("http://x", 503, {}),
        ]
        _, sleep = _fake_sleep_recorder()

        with pytest.raises(ResHttpError):
            promote_snapshot(
                snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
                discipline_code="E", revision_label="Rev A", sleep=sleep, max_attempts=3,
            )
        assert len(client.create_drawing_calls) == 3  # exactly max_attempts, not more

    def test_non_retryable_error_is_raised_immediately_without_retry(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        client.create_drawing_raises = [ResHttpError("http://x", 400, {"detail": "bad request"})]
        _, sleep = _fake_sleep_recorder()

        with pytest.raises(ResHttpError):
            promote_snapshot(
                snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
                discipline_code="E", revision_label="Rev A", sleep=sleep, max_attempts=3,
            )
        assert len(client.create_drawing_calls) == 1  # never retried

    def test_failed_promotion_never_silently_discarded_writes_failed_record(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        client.create_drawing_raises = [ResHttpError("http://x", 400, {"detail": "bad request"})]
        _, sleep = _fake_sleep_recorder()

        with pytest.raises(ResHttpError):
            promote_snapshot(
                snapshot, client, target_project_id=1, sheet_number="E0.4", drawing_title="Sheet",
                discipline_code="E", revision_label="Rev A", sleep=sleep,
            )

        log_path = promotion_log_path("fake_doc_id")
        assert log_path.exists()
        import json

        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["outcome"] == "FAILED"
        assert record["error"] is not None


class TestAuditability:
    def test_success_record_is_fully_traceable(self):
        row = _row("AH-9C")
        snapshot = _snapshot([row])
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        result = promote_snapshot(
            snapshot, client, target_project_id=7, sheet_number="E0.4", drawing_title="Sheet",
            discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        record = result.attempt
        assert record.document_id == "fake_doc_id"
        assert record.page_index == 373
        assert record.extractor_version == "dip-extract-0.1.0"
        assert record.ocr_engine == "tesseract"
        assert record.render_scale == 2.0
        assert record.target_project_id == 7
        assert record.sheet_number == "E0.4"
        assert record.revision_label == "Rev A"
        assert record.outcome == "SUCCESS"
        assert record.drawing_id == result.drawing["id"]
        assert record.drawing_version_id == result.drawing_version["id"]
        assert record.attempted_at  # non-empty ISO timestamp

    def test_promotion_log_is_append_only_across_multiple_promotions(self):
        client = FakeResClient()
        _, sleep = _fake_sleep_recorder()

        promote_snapshot(
            _snapshot([_row("AH-9C")]), client, target_project_id=1, sheet_number="E0.4",
            drawing_title="Sheet", discipline_code="E", revision_label="Rev A", sleep=sleep,
        )
        promote_snapshot(
            _snapshot([_row("AH-9C")]), client, target_project_id=1, sheet_number="E0.4",
            drawing_title="Sheet", discipline_code="E", revision_label="Rev A", sleep=sleep,
        )

        log_path = promotion_log_path("fake_doc_id")
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2  # both attempts recorded, neither overwrote the other
