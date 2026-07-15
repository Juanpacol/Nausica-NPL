"""CLI: python -m src.litminer [--gap ID ...] [--list] [--no-cache] ..."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from .report import write_reports
from .search import Cache, Gap, Miner
from .sources import ALL_SOURCES

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="litminer", description="Automated literature sourcing for research gaps."
    )
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "litminer.yaml",
        help="Gap registry YAML (default: configs/litminer.yaml)",
    )
    parser.add_argument(
        "--gap", action="append", dest="gaps", metavar="ID",
        help="Run only this gap id (repeatable). Default: all gaps.",
    )
    parser.add_argument("--list", action="store_true", help="List configured gaps and exit.")
    parser.add_argument(
        "--sources", default=None,
        help=f"Comma-separated subset of: {', '.join(ALL_SOURCES)}",
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "results" / "litminer",
        help="Output directory (default: results/litminer)",
    )
    parser.add_argument("--per-query", type=int, default=8, help="Results per query per source.")
    parser.add_argument("--top-k", type=int, default=10, help="Ranked candidates kept per gap.")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the API response cache.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    config = yaml.safe_load(args.config.read_text())
    gaps = [Gap.from_dict(d) for d in config.get("gaps", [])]

    if args.list:
        for gap in gaps:
            print(f"[{gap.priority:>8}] {gap.id} — {gap.title}")
        return 0

    if args.gaps:
        unknown = set(args.gaps) - {g.id for g in gaps}
        if unknown:
            print(f"Unknown gap id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
        gaps = [g for g in gaps if g.id in args.gaps]

    source_names = args.sources.split(",") if args.sources else None
    if source_names:
        unknown = set(source_names) - set(ALL_SOURCES)
        if unknown:
            print(f"Unknown source(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1

    cache = Cache(args.out / "cache.json", enabled=not args.no_cache)
    miner = Miner(
        source_names=source_names, cache=cache, per_query=args.per_query, top_k=args.top_k
    )

    results = []
    for i, gap in enumerate(gaps, 1):
        print(f"[{i}/{len(gaps)}] mining gap: {gap.id} ({len(gap.queries)} queries)")
        results.append(miner.run_gap(gap))

    report = write_reports(results, args.out)
    print(f"\nDone. Report: {report}")
    print(f"      BibTeX: {args.out / 'references.bib'}")
    print(f"      JSON:   {args.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
