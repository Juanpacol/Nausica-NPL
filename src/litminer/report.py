"""Render gap results as Markdown report + BibTeX + JSON."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .search import GapResult

_PRIORITY_BADGE = {"critical": "🔴 CRITICAL", "high": "🟡 HIGH", "medium": "🟠 MEDIUM", "low": "🟢 LOW"}


def write_reports(results: list[GapResult], out_dir: Path) -> Path:
    """Write report.md, references.bib and raw results.json; returns report path."""
    out_dir.mkdir(parents=True, exist_ok=True)

    report = out_dir / "report.md"
    report.write_text(render_markdown(results))

    bib_entries: list[str] = []
    seen: set[str] = set()
    for res in results:
        for paper in res.candidates:
            entry = paper.bibtex()
            if entry not in seen:
                seen.add(entry)
                bib_entries.append(entry)
    (out_dir / "references.bib").write_text("\n\n".join(bib_entries) + "\n")

    raw = [
        {
            "gap": res.gap.id,
            "priority": res.gap.priority,
            "resolved": [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "paper": r["paper"].to_dict() if r["paper"] else None,
                }
                for r in res.resolved
            ],
            "candidates": [p.to_dict() for p in res.candidates],
        }
        for res in results
    ]
    (out_dir / "results.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2))
    return report


def render_markdown(results: list[GapResult]) -> str:
    lines = [
        "# litminer — Literature Sourcing Report",
        "",
        f"Generated: {date.today().isoformat()}  ",
        "Sources: OpenAlex, Crossref, Semantic Scholar, arXiv, Europe PMC "
        "(official public APIs; no scraping).",
        "",
        "> Candidates are ranked by query relevance + citations + cross-source",
        "> corroboration. **Verify each one before citing** — open the DOI/URL,",
        "> confirm the claims match, then add it to `RESEARCH_FOCUS.md`.",
        "",
    ]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for res in sorted(results, key=lambda r: order.get(r.gap.priority, 9)):
        gap = res.gap
        lines += [
            "---",
            "",
            f"## {_PRIORITY_BADGE.get(gap.priority, gap.priority)} — {gap.title}",
            "",
            f"`gap: {gap.id}`",
            "",
        ]
        if gap.need:
            lines += [f"**What we need:** {gap.need}", ""]

        if res.resolved:
            lines += ["### Verified identifiers", ""]
            for item in res.resolved:
                paper = item["paper"]
                if paper:
                    lines.append(f"- ✅ `{item['type']}:{item['id']}` → {paper.reference_line()}")
                    if paper.abstract:
                        lines.append(f"  > {_snippet(paper.abstract)}")
                else:
                    lines.append(
                        f"- ❌ `{item['type']}:{item['id']}` — **NOT FOUND.** The identifier "
                        "in RESEARCH_FOCUS.md may be wrong; check the search candidates below."
                    )
            lines.append("")

        lines += ["### Candidates", ""]
        if not res.candidates:
            lines += ["_No results — refine the queries for this gap._", ""]
        for i, paper in enumerate(res.candidates, 1):
            cites = f" — {paper.citations} citations" if paper.citations else ""
            srcs = ", ".join(paper.sources)
            lines.append(f"{i}. {paper.reference_line()}{cites} _(via {srcs})_")
            if paper.abstract:
                lines.append(f"   > {_snippet(paper.abstract)}")
            lines.append("")
    return "\n".join(lines) + "\n"


def _snippet(text: str, max_len: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[: max_len - 1].rsplit(" ", 1)[0] + "…"
