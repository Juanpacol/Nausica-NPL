"""Cleaning, auxiliary linguistic features, and train/val/test splits.

Consolidates the raw datasets into a single texts.jsonl (input to weak_labeling.py),
and splits the weak-labeled output into train/val/test for the classifier.

Usage:
    python -m src.data_pipeline.preprocessing consolidate   # raw -> texts.jsonl
    python -m src.data_pipeline.preprocessing split          # weak_labeled.jsonl -> splits
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

URL_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"@\w+")
WHITESPACE_RE = re.compile(r"\s+")

# Auxiliary linguistic markers (features for analysis, NOT the labels themselves)
ABSOLUTISM_RE = re.compile(
    r"\b(always|never|everyone|nobody|everything|nothing|completely|totally|impossible)\b",
    re.IGNORECASE,
)
FIRST_PERSON_RE = re.compile(r"\b(i|me|my|myself|mine)\b", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Remove URLs/mentions, normalize whitespace. Keeps casing and punctuation —
    emphasis (ALL CAPS, '!!!') is signal for distortion detection, not noise."""
    text = URL_RE.sub("", text)
    text = MENTION_RE.sub("", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def linguistic_features(text: str) -> dict[str, float]:
    words = text.split()
    n = max(len(words), 1)
    return {
        "absolutism_rate": len(ABSOLUTISM_RE.findall(text)) / n,
        "first_person_rate": len(FIRST_PERSON_RE.findall(text)) / n,
        "word_count": len(words),
    }


def _extract_texts(dataset_dir: Path) -> list[dict]:
    """Pull (text, source_label) rows out of a saved HF dataset, tolerant to schema
    differences between the three source datasets."""
    from datasets import load_from_disk

    ds = load_from_disk(str(dataset_dir))
    rows = []
    for split in ds:
        for row in ds[split]:
            text = row.get("text") or row.get("Text") or row.get("post") or row.get("Context") or ""
            label = row.get("label") if "label" in row else row.get("Label")
            if isinstance(text, str) and len(text.strip()) >= 20:
                rows.append({"text": text, "source_label": label, "source": dataset_dir.name})
    return rows


def consolidate(min_length: int = 20, max_length: int = 4000) -> Path:
    """Merge raw datasets -> data/processed/texts.jsonl (cleaned, deduplicated)."""
    cfg = load_config("data")
    out_path = PROJECT_ROOT / cfg["paths"]["processed_dir"] / "texts.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    written = 0
    with open(out_path, "w") as out:
        for name, spec in cfg["datasets"].items():
            if name == "counseling_conversations":
                continue  # that one feeds dialogue_expansion, not the classifier corpus
            dataset_dir = PROJECT_ROOT / spec["local_dir"]
            if not dataset_dir.exists():
                logger.warning("%s not downloaded yet, skipping", name)
                continue
            for rec in _extract_texts(dataset_dir):
                text = clean_text(rec["text"])
                if not (min_length <= len(text) <= max_length) or text in seen:
                    continue
                seen.add(text)
                rec["text"] = text
                rec["features"] = linguistic_features(text)
                out.write(json.dumps(rec) + "\n")
                written += 1
            logger.info("consolidated %s (running total: %d)", name, written)

    logger.info("Done: %d unique texts -> %s", written, out_path)
    return out_path


def split(input_name: str = "weak_labeled.jsonl") -> None:
    """Shuffle + split weak-labeled data into train/val/test jsonl files."""
    cfg = load_config("data")
    processed = PROJECT_ROOT / cfg["paths"]["processed_dir"]
    records = [
        json.loads(line)
        for line in (processed / input_name).read_text().splitlines()
        if line.strip()
    ]
    rng = random.Random(cfg["splits"]["seed"])
    rng.shuffle(records)

    n = len(records)
    n_train = int(n * cfg["splits"]["train"])
    n_val = int(n * cfg["splits"]["val"])
    parts = {
        "train": records[:n_train],
        "val": records[n_train : n_train + n_val],
        "test": records[n_train + n_val :],
    }
    for name, rows in parts.items():
        path = processed / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        logger.info("%s: %d rows -> %s", name, len(rows), path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["consolidate", "split"])
    args = parser.parse_args()
    consolidate() if args.command == "consolidate" else split()
