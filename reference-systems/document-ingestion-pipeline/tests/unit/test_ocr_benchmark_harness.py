"""Benchmark harness logic, tested against a fake OcrEngine — no real
Tesseract/RapidOCR dependency, so this test is fast and machine-independent
regardless of what OCR engines happen to be installed."""

from PIL import Image

from dip.ocr.benchmark import run_benchmark
from dip.ocr.engines.base import OcrResult, OcrWord


class FakeAvailableEngine:
    name = "fake-available"

    def is_available(self) -> bool:
        return True

    def unavailable_reason(self) -> str | None:
        return None

    def run(self, image: Image.Image) -> OcrResult:
        return OcrResult(
            engine_name=self.name,
            full_text="AH-9C MR6",
            words=[
                OcrWord(text="AH-9C", confidence=91.0, left=0, top=0, width=10, height=5),
                OcrWord(text="MR6", confidence=88.0, left=12, top=0, width=8, height=5),
            ],
            runtime_seconds=0.01,
        )


class FakeUnavailableEngine:
    name = "fake-unavailable"

    def is_available(self) -> bool:
        return False

    def unavailable_reason(self) -> str | None:
        return "deliberately unavailable for this test"

    def run(self, image: Image.Image) -> OcrResult:  # pragma: no cover - must never be called
        raise AssertionError("run() must not be called when is_available() is False")


class FakeCrashingEngine:
    name = "fake-crashing"

    def is_available(self) -> bool:
        return True

    def unavailable_reason(self) -> str | None:
        return None

    def run(self, image: Image.Image) -> OcrResult:
        raise RuntimeError("simulated engine crash")


def _fake_raw_dir(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    return raw


def test_unavailable_engine_is_recorded_not_crashed(tmp_path, monkeypatch):
    from dip import config

    raw_dir = _fake_raw_dir(tmp_path)
    monkeypatch.setattr(
        config, "BENCHMARK_PAGES", (("missing.pdf", 0, "test page"),)
    )

    run = run_benchmark([FakeUnavailableEngine()], raw_dir=raw_dir)

    assert len(run.entries) == 1
    entry = run.entries[0]
    assert entry.engine_available is False
    assert entry.unavailable_reason == "deliberately unavailable for this test"
    assert entry.result is None


def test_missing_source_pdf_is_recorded_for_every_engine(tmp_path, monkeypatch):
    from dip import config

    raw_dir = _fake_raw_dir(tmp_path)
    monkeypatch.setattr(config, "BENCHMARK_PAGES", (("missing.pdf", 0, "test page"),))

    run = run_benchmark([FakeAvailableEngine(), FakeUnavailableEngine()], raw_dir=raw_dir)

    assert len(run.entries) == 2
    assert all(e.error is not None and "not found" in e.error for e in run.entries)


def test_one_engine_crashing_does_not_abort_the_other(tmp_path, monkeypatch):
    import pypdfium2 as pdfium

    from dip import config

    raw_dir = _fake_raw_dir(tmp_path)
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(100, 100)
    with open(raw_dir / "tiny.pdf", "wb") as f:
        pdf.save(f)
    pdf.close()

    derived = tmp_path / "derived"
    monkeypatch.setattr(config, "RENDER_CACHE_DIR", derived / "render_cache")
    monkeypatch.setattr(config, "BENCHMARK_PAGES", (("tiny.pdf", 0, "tiny test page"),))

    run = run_benchmark([FakeCrashingEngine(), FakeAvailableEngine()], raw_dir=raw_dir)

    by_engine = {e.engine_name: e for e in run.entries}
    assert by_engine["fake-crashing"].error is not None
    assert "simulated engine crash" in by_engine["fake-crashing"].error
    assert by_engine["fake-available"].result is not None
    assert by_engine["fake-available"].result.full_text == "AH-9C MR6"


def test_available_engine_produces_a_populated_result(tmp_path, monkeypatch):
    import pypdfium2 as pdfium

    from dip import config

    raw_dir = _fake_raw_dir(tmp_path)
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(100, 100)
    with open(raw_dir / "tiny.pdf", "wb") as f:
        pdf.save(f)
    pdf.close()

    derived = tmp_path / "derived"
    monkeypatch.setattr(config, "RENDER_CACHE_DIR", derived / "render_cache")
    monkeypatch.setattr(config, "BENCHMARK_PAGES", (("tiny.pdf", 0, "tiny test page"),))

    run = run_benchmark([FakeAvailableEngine()], raw_dir=raw_dir)

    assert len(run.entries) == 1
    entry = run.entries[0]
    assert entry.engine_available is True
    assert entry.result is not None
    assert len(entry.result.words) == 2
    assert entry.document_id is not None
