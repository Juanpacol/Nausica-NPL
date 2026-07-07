"""Optional human clinical review hook (Phase 5).

If psychology students/professionals become available, this exports a review sheet
(CSV) with the same rubric as llm_judge.py plus free-text fields, and can ingest the
completed sheet to compute human-vs-LLM agreement. If no reviewers are available,
this module is simply never run — the evaluation section then reports LLM-as-judge
only and lists human review as future work (see CLAUDE.md constraints).

Usage:
    python -m src.evaluation.clinical_review export --input data/synthetic/dialogues.jsonl \
        --output results/clinical_review_sheet.csv [--sample 20]
    python -m src.evaluation.clinical_review ingest --sheet results/clinical_review_sheet.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

RUBRIC_COLUMNS = ["socratic_quality", "non_directiveness", "distortion_fit"]


def export(input_path: Path, output_path: Path, sample: int | None = None) -> None:
    dialogues = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    if sample and sample < len(dialogues):
        dialogues = random.Random(42).sample(dialogues, sample)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "transcript", *RUBRIC_COLUMNS, "comments"])
        for i, d in enumerate(dialogues):
            transcript = "\n".join(f"[{t['role']}]: {t['text']}" for t in d["turns"])
            writer.writerow([i, transcript, "", "", "", ""])
    logger.info("Review sheet with %d dialogues -> %s", len(dialogues), output_path)
    logger.info("Rubric: each criterion scored 1-5 (same scale as llm_judge.py).")


def ingest(sheet_path: Path) -> None:
    with open(sheet_path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if any(r[c].strip() for c in RUBRIC_COLUMNS)]
    if not rows:
        logger.error("No completed rows found in %s", sheet_path)
        return
    means = {
        c: round(sum(int(r[c]) for r in rows) / len(rows), 2) for c in RUBRIC_COLUMNS
    }
    print(json.dumps({"n_reviewed": len(rows), "mean_scores": means}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_export = sub.add_parser("export")
    p_export.add_argument("--input", type=Path, required=True)
    p_export.add_argument("--output", type=Path, required=True)
    p_export.add_argument("--sample", type=int, default=None)
    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("--sheet", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export":
        export(args.input, args.output, args.sample)
    else:
        ingest(args.sheet)
