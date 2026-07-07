"""Unsupervised mindset profiling with BERTopic (Phase 3).

Complements the supervised classifier: clusters depression-labeled texts into
qualitative "thinking profiles" (e.g., hopelessness vs self-blame clusters) for the
paper's qualitative analysis section.

Requires the optional extra:  pip install -e ".[clustering]"
Usage: python -m src.models.mindset_profiler --input data/processed/texts.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.utils.config import PROJECT_ROOT
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MindsetProfiler:
    def __init__(self, min_topic_size: int = 15):
        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "BERTopic not installed — run: pip install -e '.[clustering]'"
            ) from e

        self._topic_model = BERTopic(
            embedding_model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2"),
            language="english",
            min_topic_size=min_topic_size,
            calculate_probabilities=False,
        )
        self._fitted = False

    def fit(self, texts: list[str]):
        logger.info("Fitting BERTopic on %d texts ...", len(texts))
        topics, _ = self._topic_model.fit_transform(texts)
        self._fitted = True
        info = self._topic_model.get_topic_info()
        logger.info("Found %d topics (plus outlier topic -1)", len(info) - 1)
        return info

    def profile(self, text: str) -> dict:
        if not self._fitted:
            raise RuntimeError("Call fit() first")
        topics, _ = self._topic_model.transform([text])
        topic_id = int(topics[0])
        keywords = [w for w, _ in (self._topic_model.get_topic(topic_id) or [])][:8]
        return {"topic_id": topic_id, "keywords": keywords}

    def save(self, path: str | Path):
        self._topic_model.save(str(path), serialization="safetensors")
        logger.info("Saved topic model -> %s", path)


def run(input_path: Path, output_dir: Path) -> None:
    records = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    texts = [r["text"] for r in records]

    profiler = MindsetProfiler()
    info = profiler.fit(texts)

    output_dir.mkdir(parents=True, exist_ok=True)
    info.to_csv(output_dir / "topic_info.csv", index=False)
    profiler.save(output_dir / "bertopic_model")
    logger.info("Topic summary -> %s", output_dir / "topic_info.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results" / "mindset_profiles")
    args = parser.parse_args()
    run(args.input, args.output_dir)
