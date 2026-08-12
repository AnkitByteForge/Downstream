"""Field-level normalization and validation — pure functions, no OCR, no
grid dependency. Every rule here is additive (flag, don't fix) per the
approved decisions: numeric normalization never fabricates a value,
MCA<=FLA is flagged not corrected, missing values stay null, and tag
pattern mismatches are advisory only.
"""

from __future__ import annotations

import re

# The AH-* pattern actually observed on the real E0.4 sheet during the
# Phase C investigation (e.g. AH-9C, AH-24CTA, AH-UP, AH-CAN) — advisory
# only (decision 15): a non-matching tag is flagged, never rejected, since
# a real tag could legitimately not match an assumed pattern.
TAG_PATTERN = re.compile(r"^AH-[A-Z0-9]+$", re.IGNORECASE)

# Unanchored counterpart used by build.py to locate the real tag *within*
# noisy OCR text, rather than requiring the whole cell string to match.
# Measured, not assumed: real-data runs against the actual E0.4 sheet found
# Tesseract intermittently prepending a single stray punctuation-like
# character to this specific column across different runs (observed both
# U+FFFD and U+2018 on the same cell on different passes) — not a fixed,
# whitelistable character set, so edge-character stripping alone isn't
# robust. Searching for the known-valid tag shape and extracting just that
# substring is not fabricating a value: the digits/letters themselves were
# never wrong in either observed case, only an adjacent, non-content glyph
# was.
TAG_SEARCH_PATTERN = re.compile(r"AH-[A-Z0-9]+", re.IGNORECASE)

_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")
# Characters stripped ONLY from the two ends of the raw string before the
# fullmatch check below — never from the middle. Measured, not assumed: a
# real-data test run against the actual E0.4 sheet showed OCR occasionally
# appends a stray bracket/pipe character adjacent to a ruling-line-crossing
# cell (e.g. "56.0|", "27.0["), almost certainly the grid's own vertical
# rule line being misread as a stray glyph. Stripping only leading/trailing
# noise, then requiring the *entire remainder* to be one clean number, is
# still "never coerce a jumbled value" — a token like "5]8.0" (junk in the
# middle, not the edges) is correctly left unparseable, still None.
_EDGE_NOISE_CHARS = " \t\r\n[]{}|"


def normalize_numeric(raw: str | None) -> float | None:
    """Parses a raw OCR string into a float, or returns None if it doesn't
    contain a clean number. Never coerces, never guesses — a raw value like
    '-' or 'TBD' or an empty string correctly produces None, and the raw
    text itself is preserved separately by the caller (decision 12)."""
    if raw is None:
        return None
    stripped = raw.strip(_EDGE_NOISE_CHARS)
    if not stripped or stripped in ("-", "?", "TBD", "N/A"):
        return None
    match = _NUMERIC_RE.fullmatch(stripped)
    if not match:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def check_mca_fla_suspicious(mca_numeric: float | None, fla_numeric: float | None) -> bool:
    """True only when BOTH parsed and mca_numeric <= fla_numeric — real
    electrical convention is MCA > FLA (MCA includes a safety factor over
    FLA). Flags, never corrects (decision 13). Returns False, not an
    error, when either value is missing/unparsed — there is nothing
    suspicious to report about a value that isn't there."""
    if mca_numeric is None or fla_numeric is None:
        return False
    return mca_numeric <= fla_numeric


def check_tag_pattern(tag: str) -> bool:
    """Returns the tag_pattern_flag value: True means the tag did NOT match
    the observed pattern (worth a human glance), False means it matched.
    Advisory only — never used to reject a row (decision 15)."""
    return TAG_PATTERN.match(tag.strip()) is None
