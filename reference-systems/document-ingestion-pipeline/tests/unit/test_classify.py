"""Pure logic tests for the page classification heuristic — no PDF, no I/O."""

from dip.manifest.classify import PageStats, classify_page


def test_native_text_page():
    stats = PageStats(char_len=2500, image_coverage_pct=0.0, path_object_count=50)
    classification, needs_ocr = classify_page(stats)
    assert classification == "native_text"
    assert needs_ocr is False


def test_raster_embedded_schedule_page():
    # E0.4-shaped: real numbers from the DSH corpus (~37.5% image coverage).
    stats = PageStats(char_len=1480, image_coverage_pct=37.53, path_object_count=3259)
    classification, needs_ocr = classify_page(stats)
    assert classification == "raster_embedded"
    assert needs_ocr is True


def test_vector_curve_page():
    # EE5.1-shaped: real numbers from the DSH corpus (near-zero text, huge path count).
    stats = PageStats(char_len=462, image_coverage_pct=0.58, path_object_count=41070)
    classification, needs_ocr = classify_page(stats)
    assert classification == "vector_curve"
    assert needs_ocr is True


def test_ambiguous_page_is_conservative_not_silently_native():
    # Below every named threshold on every axis -> "mixed", flagged for OCR
    # rather than silently assumed fine.
    stats = PageStats(char_len=50, image_coverage_pct=5.0, path_object_count=100)
    classification, needs_ocr = classify_page(stats)
    assert classification == "mixed"
    assert needs_ocr is True


def test_raster_threshold_is_a_strict_floor_not_a_guess():
    just_under = PageStats(char_len=2000, image_coverage_pct=19.99, path_object_count=10)
    just_over = PageStats(char_len=2000, image_coverage_pct=20.0, path_object_count=10)
    assert classify_page(just_under)[0] == "native_text"
    assert classify_page(just_over)[0] == "raster_embedded"
