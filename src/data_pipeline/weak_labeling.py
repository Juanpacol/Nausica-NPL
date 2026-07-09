"""LLM-as-annotator: tag texts with the 5-type cognitive distortion taxonomy.

No clinician-annotated English dataset exists at the scale we need, so we weak-label
with an LLM (documented limitation — see CLAUDE.md). Each text gets multi-label tags
with per-label confidence; labels under the configured threshold are dropped. A
spot-check sample is written alongside the output for mandatory manual review.

Usage:
    python -m src.data_pipeline.weak_labeling --input data/processed/texts.jsonl \
        --output data/processed/weak_labeled.jsonl [--limit 100]

Input format:  one JSON object per line with at least {"text": ...}
Output format: input fields + {"distortions": {label: confidence}, "labels": [...]}
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.utils.config import load_config, taxonomy_labels
from src.utils.llm_client import LLMClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert annotator of cognitive distortions in text, \
trained on Beck's cognitive therapy framework. You label texts with these 5 distortion \
types (a text may have several, or none):

1. all_or_nothing — absolute binary thinking (always/never/completely/ruined)
2. overgeneralization — sweeping permanent conclusions from single events
3. emotional_reasoning — treating feelings as evidence of facts
4. catastrophizing — expecting/inflating worst-case outcomes, "what if" spirals
5. mind_reading — assuming without evidence what others think (negatively)

Respond ONLY with a JSON object mapping each of the 5 labels to a confidence in [0,1].
Example: {"all_or_nothing": 0.9, "overgeneralization": 0.1, "emotional_reasoning": 0.0, \
"catastrophizing": 0.7, "mind_reading": 0.0}"""

FEW_SHOT = """Examples:

Text: "I failed the exam. I fail everything I ever try, there's no point anymore."
{"all_or_nothing": 0.7, "overgeneralization": 0.95, "emotional_reasoning": 0.1, "catastrophizing": 0.3, "mind_reading": 0.0}

Text: "My boss didn't say hi today. He must think I'm useless and is planning to fire me."
{"all_or_nothing": 0.0, "overgeneralization": 0.1, "emotional_reasoning": 0.2, "catastrophizing": 0.6, "mind_reading": 0.95}

Text: "Had a rough day at work but tomorrow is a new chance."
{"all_or_nothing": 0.0, "overgeneralization": 0.0, "emotional_reasoning": 0.0, "catastrophizing": 0.0, "mind_reading": 0.0}

Now annotate this text:
"""


def label_text(client: LLMClient, text: str) -> dict[str, float]:
    """Return {label: confidence} for one text, validated against the taxonomy."""
    raw = client.complete_json(FEW_SHOT + json.dumps(text), system=SYSTEM_PROMPT)
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object, got: {type(raw)}")
    labels = taxonomy_labels()
    return {label: float(max(0.0, min(1.0, raw.get(label, 0.0)))) for label in labels}


def run(input_path: Path, output_path: Path, limit: int | None = None) -> None:
    cfg = load_config("data")["weak_labeling"]
    client = LLMClient(model=cfg["model"])
    threshold = cfg["confidence_threshold"]

    records = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    # Deterministic shuffle so --limit N is a random sample, not a head slice —
    # source datasets are ordered by category and a head slice would be one-class.
    random.Random(42).shuffle(records)
    if limit:
        records = records[:limit]
    logger.info("Weak-labeling %d texts (threshold=%.2f)", len(records), threshold)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    labeled = []
    with open(output_path, "w") as out:
        for i, rec in enumerate(records):
            try:
                confidences = label_text(client, rec["text"])
            except Exception as e:  # noqa: BLE001 — skip bad rows, keep the run alive
                logger.warning("row %d failed: %s", i, e)
                continue
            rec["distortions"] = confidences
            rec["labels"] = [k for k, v in confidences.items() if v >= threshold]
            out.write(json.dumps(rec) + "\n")
            labeled.append(rec)
            if (i + 1) % 50 == 0:
                logger.info("  %d/%d done — %s", i + 1, len(records), client.usage_summary())

    # Mandatory manual review sample (agreement rate goes in docs/DATA_QUALITY.md)
    sample_size = max(1, int(len(labeled) * cfg["spot_check_fraction"]))
    sample = random.Random(42).sample(labeled, min(sample_size, len(labeled)))
    spot_path = output_path.with_name(output_path.stem + "_spotcheck.jsonl")
    spot_path.write_text("".join(json.dumps(r) + "\n" for r in sample))

    logger.info("Done. %d labeled -> %s | %d for spot-check -> %s | %s",
                len(labeled), output_path, len(sample), spot_path, client.usage_summary())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None, help="cap rows (for cheap dry runs)")
    args = parser.parse_args()
    run(args.input, args.output, args.limit)
