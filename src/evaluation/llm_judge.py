"""LLM-as-judge scoring of reframing dialogues (Phase 5, mandatory eval floor).

Scores each dialogue on a 3-criterion rubric (1-5 each):
- socratic_quality: open questions that examine evidence/alternatives vs lecturing
- non_directiveness: guides discovery vs pushing advice or dismissing feelings
- distortion_fit: counselor turns actually engage the client's distorted framing

Usage:
    python -m src.evaluation.llm_judge --input data/synthetic/dialogues.jsonl \
        --output results/judge_scores.jsonl [--limit 20]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.utils.config import load_config
from src.utils.llm_client import LLMClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

RUBRIC_SYSTEM = """You are an expert evaluator of CBT counseling dialogues. Score the \
counselor's performance in the dialogue on three criteria, each an integer 1-5:

- socratic_quality: 5 = consistently open, evidence-examining questions; 1 = lectures or \
closed questions only.
- non_directiveness: 5 = guides the client's own discovery, validates feelings; 1 = pushes \
direct advice or dismisses the client.
- distortion_fit: 5 = counselor turns clearly engage the client's specific distorted \
framing (absolutism, catastrophizing, etc.); 1 = generic support unrelated to the framing.

Respond ONLY with JSON:
{"socratic_quality": n, "non_directiveness": n, "distortion_fit": n, "rationale": "one sentence"}"""


def judge_dialogue(client: LLMClient, turns: list[dict]) -> dict:
    transcript = "\n".join(f"[{t['role']}]: {t['text']}" for t in turns)
    result = client.complete_json(f"Dialogue to evaluate:\n\n{transcript}", system=RUBRIC_SYSTEM)
    if not isinstance(result, dict):
        raise ValueError("Judge did not return a JSON object")
    for key in ("socratic_quality", "non_directiveness", "distortion_fit"):
        score = int(result.get(key, 0))
        if not 1 <= score <= 5:
            raise ValueError(f"Score out of range for {key}: {result.get(key)}")
        result[key] = score
    return result


def run(input_path: Path, output_path: Path, limit: int | None = None) -> None:
    dialogues = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    if limit:
        dialogues = dialogues[:limit]

    judge_cfg = load_config("data")["judge"]
    client = LLMClient(model=judge_cfg["model"], provider=judge_cfg.get("provider"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    totals = {"socratic_quality": 0, "non_directiveness": 0, "distortion_fit": 0}
    judged = 0
    with open(output_path, "w") as out:
        for i, d in enumerate(dialogues):
            try:
                scores = judge_dialogue(client, d["turns"])
            except Exception as e:  # noqa: BLE001 — skip bad rows, keep the run alive
                logger.warning("dialogue %d failed: %s", i, e)
                continue
            out.write(json.dumps({"index": i, **scores}) + "\n")
            for k in totals:
                totals[k] += scores[k]
            judged += 1

    if judged:
        means = {k: round(v / judged, 2) for k, v in totals.items()}
        logger.info("Judged %d dialogues. Mean scores: %s | %s",
                    judged, means, client.usage_summary())
        print(json.dumps({"n": judged, "mean_scores": means}, indent=2))
    else:
        logger.error("No dialogues were successfully judged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.input, args.output, args.limit)
