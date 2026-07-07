"""Contrastive rigidity embedding (Phase 2, pillar 3).

Fine-tunes a MiniLM sentence encoder so that rigid formulations and their flexible
reformulations structure the embedding space, then scores any text by projecting
its embedding onto the rigid→flexible centroid axis:

    rigidity_score(text) = normalize( (emb(text) - flexible_centroid) · axis )

Higher = more rigid, in [0, 1]. This is a label-light operationalization of
cognitive rigidity that cross-validates the classifier-based CFI (convergent
validity — see docs/VALIDATION.md).

LIMITATION (disclose): the (rigid, flexible) pairs are synthetic LLM reformulations
extracted from generated dialogues, not clinician-authored reframes.

Train: python -m src.models.rigidity_embedding train
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _project(embedding: np.ndarray, flexible_centroid: np.ndarray, axis: np.ndarray,
             proj_min: float, proj_max: float) -> float:
    """Pure projection + min-max normalization; unit-testable without any model.

    axis = rigid_centroid - flexible_centroid. Score 0 ~ flexible end, 1 ~ rigid end.
    """
    span = proj_max - proj_min
    if span <= 0:
        raise ValueError("Degenerate projection range (proj_max <= proj_min)")
    raw = float(np.dot(embedding - flexible_centroid, axis))
    return float(min(1.0, max(0.0, (raw - proj_min) / span)))


class RigidityEmbedder:
    def __init__(self, model=None, flexible_centroid=None, axis=None,
                 proj_min=0.0, proj_max=1.0):
        self.model = model
        self.flexible_centroid = flexible_centroid
        self.axis = axis
        self.proj_min = proj_min
        self.proj_max = proj_max

    # ------------------------------------------------------------------ fitting

    def fit(self, pairs: list[dict], cfg: dict) -> dict:
        """Fine-tune contrastively, build the projection axis, return val metrics."""
        from sentence_transformers import InputExample, SentenceTransformer, losses
        from torch.utils.data import DataLoader

        rng = random.Random(cfg["seed"])
        pairs = list(pairs)
        rng.shuffle(pairs)
        n_val = max(1, int(len(pairs) * cfg["val_fraction"]))
        val_pairs, train_pairs = pairs[:n_val], pairs[n_val:]
        logger.info("Pairs: %d train / %d val", len(train_pairs), len(val_pairs))

        # Baseline: un-finetuned model with the same centroid procedure
        base = SentenceTransformer(cfg["base_model"])
        base_acc = self._ordering_accuracy(base, train_pairs, val_pairs)

        # Fine-tune
        self.model = SentenceTransformer(cfg["base_model"])
        examples = [InputExample(texts=[p["rigid"], p["flexible"]]) for p in train_pairs]
        batch_size = min(cfg["batch_size"], len(examples))
        loader = DataLoader(examples, shuffle=True, batch_size=batch_size)
        loss = losses.MultipleNegativesRankingLoss(self.model)
        self.model.fit(
            train_objectives=[(loader, loss)],
            epochs=cfg["epochs"],
            show_progress_bar=False,
        )

        self._build_projection(self.model, train_pairs)
        tuned_acc = self._val_ordering_accuracy(val_pairs)

        return {
            "n_train_pairs": len(train_pairs),
            "n_val_pairs": len(val_pairs),
            "ordering_acc_finetuned": round(tuned_acc, 4),
            "ordering_acc_base": round(base_acc, 4),
            "limitation": "pairs are synthetic LLM reformulations, not clinician-authored",
        }

    def _build_projection(self, model, train_pairs: list[dict]) -> None:
        rigid_emb = model.encode([p["rigid"] for p in train_pairs])
        flex_emb = model.encode([p["flexible"] for p in train_pairs])
        rigid_centroid = rigid_emb.mean(axis=0)
        self.flexible_centroid = flex_emb.mean(axis=0)
        self.axis = rigid_centroid - self.flexible_centroid
        raws = [
            float(np.dot(e - self.flexible_centroid, self.axis))
            for e in np.concatenate([rigid_emb, flex_emb])
        ]
        self.proj_min, self.proj_max = min(raws), max(raws)

    def _ordering_accuracy(self, model, train_pairs, val_pairs) -> float:
        """Ordering accuracy for an arbitrary model using centroids from train_pairs."""
        probe = RigidityEmbedder(model=model)
        probe._build_projection(model, train_pairs)
        return probe._val_ordering_accuracy(val_pairs)

    def _val_ordering_accuracy(self, val_pairs: list[dict]) -> float:
        correct = sum(
            1 for p in val_pairs
            if self.rigidity_score(p["rigid"]) > self.rigidity_score(p["flexible"])
        )
        return correct / len(val_pairs)

    # ---------------------------------------------------------------- scoring

    def rigidity_score(self, text: str | list[str]) -> float | list[float]:
        if isinstance(text, list):
            return [self.rigidity_score(t) for t in text]
        emb = self.model.encode([text])[0]
        return _project(emb, self.flexible_centroid, self.axis, self.proj_min, self.proj_max)

    # ------------------------------------------------------------- persistence

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        self.model.save(str(out_dir / "model"))
        (out_dir / "projection.json").write_text(json.dumps({
            "flexible_centroid": self.flexible_centroid.tolist(),
            "axis": self.axis.tolist(),
            "proj_min": self.proj_min,
            "proj_max": self.proj_max,
        }))

    @classmethod
    def load(cls, path: str | Path | None = None) -> "RigidityEmbedder":
        from sentence_transformers import SentenceTransformer

        cfg = load_config("model")["contrastive_embedding"]
        out_dir = Path(path) if path else PROJECT_ROOT / cfg["output_dir"]
        proj_file = out_dir / "projection.json"
        if not proj_file.exists():
            raise FileNotFoundError(f"No trained rigidity embedding at {out_dir}")
        proj = json.loads(proj_file.read_text())
        return cls(
            model=SentenceTransformer(str(out_dir / "model")),
            flexible_centroid=np.array(proj["flexible_centroid"]),
            axis=np.array(proj["axis"]),
            proj_min=proj["proj_min"],
            proj_max=proj["proj_max"],
        )


# --------------------------------------------------------------------- training


def train() -> dict:
    from scipy.stats import pearsonr

    cfg = load_config("model")["contrastive_embedding"]
    data_cfg = load_config("data")
    pairs_path = PROJECT_ROOT / data_cfg["paths"]["processed_dir"] / "contrastive_pairs.jsonl"
    pairs = [json.loads(line) for line in pairs_path.read_text().splitlines() if line.strip()]

    embedder = RigidityEmbedder()
    metrics = embedder.fit(pairs, cfg)

    # Convergent validity vs classifier-based CFI. The distortion classifier head is
    # currently UNTRAINED (probs ~0.5) — r will be near-meaningless until Phase 1
    # fine-tuning lands; reported as-is with the caveat flag.
    from src.metrics.cognitive_flexibility_index import compute_cfi
    from src.models.distortion_classifier import DistortionClassifier

    classifier = DistortionClassifier.load()
    texts = [p["rigid"] for p in pairs] + [p["flexible"] for p in pairs]
    emb_scores = embedder.rigidity_score(texts)
    cfi_scores = [compute_cfi(classifier.predict(t)) for t in texts]
    r, p_value = pearsonr(emb_scores, cfi_scores)
    metrics["pearson_r_vs_cfi"] = round(float(r), 4)
    metrics["pearson_p_value"] = round(float(p_value), 4)
    metrics["classifier_untrained"] = True

    out_dir = PROJECT_ROOT / cfg["output_dir"]
    embedder.save(out_dir)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    logger.info("Saved embedder -> %s", out_dir)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train"])
    parser.parse_args()
    train()
