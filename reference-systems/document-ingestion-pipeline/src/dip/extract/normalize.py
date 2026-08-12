"""Field-level normalization and validation — pure functions, no OCR, no
grid dependency. Every rule here is additive (flag, don't fix) per the
approved decisions: numeric normalization never fabricates a value,
MCA<=FLA is flagged not corrected, missing values stay null, and tag
pattern mismatches are advisory only.

Phase C reliability milestone: adds an explicit per-field ValidationStatus
(VALID/AMBIGUOUS/INVALID, plus MISSING for a genuinely empty cell) computed
by a FIELD-SPECIFIC pattern for each New Unit column — not one generic
numeric function reused everywhere, because the fields' real shapes differ
(breaker_rating is "25/3", not a number; conduit is "1 in", not bare digits;
volts is a bare integer; fla/mca are decimals). No validator here ever
repairs a value — every one only classifies the *already-extracted* raw
text and, for fla/mca, the already-parsed numeric value.
"""

from __future__ import annotations

import re

from dip.provenance import ValidationStatus

# Recognized explicit non-value placeholders — the source itself is saying
# "not applicable / not yet determined" here, not garbled OCR. Classified
# INVALID (a real value the field's own semantics require is not present),
# distinct from MISSING (no OCR text at all — the cell was empty).
PLACEHOLDER_TOKENS = frozenset({"-", "?", "tbd", "n/a", ""})

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


# --- Field-specific patterns, one per New Unit column, per Task 4 -----
# Each pattern reflects the field's own real shape, observed directly on
# the real E0.4 sheet (ground-truth-verified values) — never a generic
# numeric/text catch-all applied uniformly.
FED_FROM_PANEL_PATTERN = re.compile(r"^MR\d+$", re.IGNORECASE)  # e.g. "MR4", "MR12"
BREAKER_RATING_PATTERN = re.compile(r"^\d+/\d+$")  # e.g. "60/3", "25/3" — the "/" is load-bearing
CONDUIT_PATTERN = re.compile(r"^(\d+(/\d+)?)\s*in$", re.IGNORECASE)  # e.g. "1 in", "3/4 in", "1/2 in"
VOLTS_PATTERN = re.compile(r"^\d+$")  # e.g. "480", "208"


def _validate_pattern_field(raw: str | None, pattern: re.Pattern[str]) -> ValidationStatus:
    """Generic engine behind the field-specific validators below — never
    called directly on a field with different semantics; each field gets
    its own named wrapper so the *reason* a given pattern applies stays
    attached to the field it describes (Task 4).

    Strips the same *edge*-only noise characters normalize_numeric()
    already tolerates (measured real OCR artifact — a stray bracket/pipe
    adjacent to a ruling-line-crossing cell) before the pattern check —
    this affects only which ValidationStatus is returned, never what's
    stored in the field's own raw value (the caller keeps the untouched
    OCR text separately)."""
    if raw is None:
        return "MISSING"
    stripped = raw.strip().strip(_EDGE_NOISE_CHARS)
    if stripped.lower() in PLACEHOLDER_TOKENS:
        return "INVALID"
    if pattern.fullmatch(stripped):
        return "VALID"
    return "AMBIGUOUS"


def validate_fed_from_panel(raw: str | None) -> ValidationStatus:
    """New Unit 'Fed From Panel' — every ground-truth-verified value on the
    real E0.4 sheet is 'MR<digits>'. A value that doesn't match is flagged,
    never discarded — a real panel name outside this convention is possible
    and must still be preserved verbatim in the raw field."""
    return _validate_pattern_field(raw, FED_FROM_PANEL_PATTERN)


def validate_breaker_rating(raw: str | None) -> ValidationStatus:
    """New Unit 'Circuit Breaker Rating' — 'amperage/poles', e.g. '60/3'.
    The real, observed E0.4 failure this guards against directly: OCR
    misreading the '/' as '1' (e.g. real '25/3' read as '2513') produces
    text with the right digits but the wrong shape — this validator flags
    exactly that case as AMBIGUOUS rather than accepting '2513' as if it
    were a normally-shaped rating. It never attempts to reinsert the '/'."""
    return _validate_pattern_field(raw, BREAKER_RATING_PATTERN)


def validate_conduit(raw: str | None) -> ValidationStatus:
    """New Unit 'Conduit' — a size plus the literal unit 'in', e.g. '1 in',
    '3/4 in'. The unit is load-bearing and must never be stripped."""
    return _validate_pattern_field(raw, CONDUIT_PATTERN)


def validate_volts(raw: str | None) -> ValidationStatus:
    """New Unit 'Volts' — a bare integer on every ground-truth-verified
    E0.4 row (480). Kept as its own validator (not reusing the fla/mca
    numeric path) because volts has no decimal-point failure mode to guard
    against and no plausibility cross-check against another field."""
    return _validate_pattern_field(raw, VOLTS_PATTERN)


# Real NEC/electrical convention: MCA (Minimum Circuit Ampacity) includes a
# safety factor over FLA (Full Load Amps) and is typically ~1.0-1.3x FLA.
# This ratio is generous headroom above that (real engineered systems can
# legitimately exceed it) while still catching the actual, observed
# dropped-decimal failure mode (a real "22.0" OCR'd as "220" against a real
# FLA of "21.0" produces a ~10x ratio — comfortably past this floor). This
# is a plausibility FLAG, never a correction: the numeric value returned by
# normalize_numeric() is never altered by this check.
MCA_FLA_MAX_PLAUSIBLE_RATIO = 3.0


def validate_numeric_field(raw: str | None, other_numeric_for_ratio_check: float | None = None) -> ValidationStatus:
    """FLA/MCA — a decimal number. VALID if normalize_numeric() parses it
    cleanly with a plausible magnitude; AMBIGUOUS if it parses but is
    implausibly large relative to the paired field (the dropped-decimal
    signature); INVALID for a recognized non-value placeholder; MISSING if
    the cell had no OCR text at all. Never returns a different number than
    normalize_numeric() would — this function only classifies, never
    repairs."""
    if raw is None:
        return "MISSING"
    stripped = raw.strip()
    if stripped.lower() in PLACEHOLDER_TOKENS:
        return "INVALID"
    value = normalize_numeric(raw)
    if value is None:
        return "AMBIGUOUS"  # present, non-placeholder, but didn't parse as a clean number
    if other_numeric_for_ratio_check is not None and other_numeric_for_ratio_check > 0:
        ratio = value / other_numeric_for_ratio_check
        if ratio > MCA_FLA_MAX_PLAUSIBLE_RATIO or ratio < (1.0 / MCA_FLA_MAX_PLAUSIBLE_RATIO):
            return "AMBIGUOUS"
    return "VALID"
