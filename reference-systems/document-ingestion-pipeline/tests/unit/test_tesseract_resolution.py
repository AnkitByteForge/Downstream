"""dip.config.resolve_tesseract_cmd() and TesseractEngine.is_available() —
tested via monkeypatching, without depending on whether Tesseract is
actually installed on the machine running the test."""

from dip import config
from dip.ocr.engines.tesseract_engine import TesseractEngine


def test_env_var_override_wins_when_it_points_to_a_real_file(tmp_path, monkeypatch):
    fake_binary = tmp_path / "fake_tesseract.exe"
    fake_binary.write_text("not a real binary, just needs to exist")
    monkeypatch.setenv(config.TESSERACT_CMD_ENV_VAR, str(fake_binary))

    assert config.resolve_tesseract_cmd() == str(fake_binary)


def test_env_var_pointing_nowhere_falls_through(tmp_path, monkeypatch):
    monkeypatch.setenv(config.TESSERACT_CMD_ENV_VAR, str(tmp_path / "does_not_exist.exe"))
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(config, "TESSERACT_DEFAULT_CANDIDATES", ())

    assert config.resolve_tesseract_cmd() is None


def test_engine_reports_unavailable_cleanly_when_nothing_resolves(monkeypatch):
    monkeypatch.setattr(config, "resolve_tesseract_cmd", lambda: None)

    engine = TesseractEngine()
    assert engine.is_available() is False
    assert engine.unavailable_reason() is not None
    assert "README" in engine.unavailable_reason()


def test_engine_reports_available_when_a_command_resolves(monkeypatch):
    monkeypatch.setattr(config, "resolve_tesseract_cmd", lambda: "C:\\fake\\tesseract.exe")

    engine = TesseractEngine()
    assert engine.is_available() is True
    assert engine.unavailable_reason() is None
