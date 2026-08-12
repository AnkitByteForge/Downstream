"""Renders a BenchmarkRun as a plain-Markdown report.

No accuracy percentage is ever computed or written here — only measured
runtimes, word counts, confidence where the engine reports one, and
presence/absence of a small set of known tokens already hand-verified in
docs/research/DSH_Atascadero_Reconnaissance.md, explicitly labeled as a
coarse spot-check, never an accuracy figure.
"""

from __future__ import annotations

from dip.ocr.benchmark import BenchmarkEntry, BenchmarkRun

# Known tokens per page, taken directly from what the reconnaissance report
# already hand-read from these exact sheets — used only as a presence
# spot-check, never as a scored accuracy metric.
KNOWN_TOKENS = {
    373: ["AH-9C", "MR6", "MR7", "MRDP"],  # E0.4
    375: ["MR1", "MR4", "MR6", "MRDP"],  # E0.6
    43: ["MRDP", "MVDS-1", "MVGPS2"],  # EE5.1
}


def _token_spotcheck(entry: BenchmarkEntry) -> list[tuple[str, bool]]:
    if entry.result is None:
        return []
    joined = entry.result.full_text.upper()
    tokens = KNOWN_TOKENS.get(entry.page_index, [])
    return [(tok, tok in joined) for tok in tokens]


def render_markdown(run: BenchmarkRun) -> str:
    lines: list[str] = []
    lines.append(f"# DIP Phase B — OCR Benchmark Results ({run.run_id})")
    lines.append("")
    lines.append(
        "No accuracy percentage is claimed anywhere in this report — only measured "
        "runtime, word counts, engine-reported confidence where available, and a "
        "presence/absence spot-check against tokens the reconnaissance report already "
        "hand-verified on these exact pages. This is a coarse proxy, not a rigorous "
        "accuracy measurement."
    )
    lines.append("")

    lines.append("## Summary table")
    lines.append("")
    lines.append("| Page | Engine | Available | Runtime (s) | Words found | Avg confidence |")
    lines.append("|---|---|---|---|---|---|")
    for entry in run.entries:
        if entry.result is not None:
            confs = [w.confidence for w in entry.result.words if w.confidence is not None]
            avg_conf = f"{sum(confs) / len(confs):.1f}" if confs else "n/a"
            lines.append(
                f"| {entry.page_label} | {entry.engine_name} | yes | "
                f"{entry.result.runtime_seconds:.2f} | {len(entry.result.words)} | {avg_conf} |"
            )
        else:
            lines.append(
                f"| {entry.page_label} | {entry.engine_name} | **no** | - | - | - "
                f"({entry.unavailable_reason or entry.error or 'unknown'}) |"
            )
    lines.append("")

    lines.append("## Engine availability")
    lines.append("")
    seen_engines: dict[str, BenchmarkEntry] = {}
    for entry in run.entries:
        seen_engines.setdefault(entry.engine_name, entry)
    for name, entry in seen_engines.items():
        status = "available" if entry.engine_available else f"**unavailable** — {entry.unavailable_reason}"
        lines.append(f"- `{name}`: {status}")
    lines.append("")

    lines.append("## Per-page detail")
    lines.append("")
    for entry in run.entries:
        lines.append(f"### {entry.page_label} — `{entry.engine_name}`")
        lines.append("")
        if entry.error and entry.result is None:
            lines.append(f"**Error:** {entry.error}")
            lines.append("")
            continue
        if entry.result is None:
            lines.append(f"Skipped — {entry.unavailable_reason}")
            lines.append("")
            continue

        lines.append(f"- Runtime: {entry.result.runtime_seconds:.2f}s")
        lines.append(f"- Words found: {len(entry.result.words)}")

        spotcheck = _token_spotcheck(entry)
        if spotcheck:
            lines.append("- Known-token spot-check (presence only, not an accuracy score):")
            for token, found in spotcheck:
                mark = "found" if found else "NOT found"
                lines.append(f"  - `{token}`: {mark}")

        sample = entry.result.full_text[:400].replace("\n", " ")
        lines.append(f"- First ~400 chars of extracted text: `{sample}`")
        lines.append("")

    lines.append("## Comparison notes")
    lines.append("")
    lines.append(
        "Fill in by hand after reviewing the per-page detail above: which engine's "
        "table/column structure is more reconstructable, which produced obvious "
        "garbling on dense small-font values, and which known tokens either engine "
        "missed entirely."
    )
    lines.append("")

    return "\n".join(lines)
