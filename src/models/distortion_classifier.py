"""Multi-label cognitive distortion classifier (Phase 2).

Fine-tunes mental/mental-roberta-base (CC-BY-NC-4.0, gated — docs/LICENSING.md; falls
back to roberta-base if the gate is unavailable) with a sigmoid multi-label head over
the 5-type taxonomy. Training data comes from weak_labeling.py output.

Train:    python -m src.models.distortion_classifier train
Predict:  DistortionClassifier.load(...).predict("text") -> {label: prob}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from src.utils.config import PROJECT_ROOT, load_config, taxonomy_labels
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _load_base(model_cfg: dict, num_labels: int):
    """Load the configured encoder, falling back if the gated model is unreachable."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    for name in (model_cfg["encoder"]["base_model"], model_cfg["encoder"]["fallback_model"]):
        try:
            tokenizer = AutoTokenizer.from_pretrained(name)
            model = AutoModelForSequenceClassification.from_pretrained(
                name, num_labels=num_labels, problem_type="multi_label_classification"
            )
            logger.info("Loaded encoder: %s", name)
            return tokenizer, model
        except Exception as e:  # noqa: BLE001 — gated model may 403 without HF_TOKEN
            logger.warning("Could not load %s (%s), trying fallback", name, e)
    raise RuntimeError("No encoder could be loaded — check HF_TOKEN and network")


class DistortionClassifier:
    """Inference wrapper. Use .load() for a fine-tuned checkpoint, or train first."""

    def __init__(self, model, tokenizer, max_length: int = 256):
        self.model = model
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.labels = taxonomy_labels()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    @classmethod
    def load(cls, checkpoint_dir: str | Path | None = None) -> "DistortionClassifier":
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        cfg = load_config("model")
        path = Path(checkpoint_dir) if checkpoint_dir else PROJECT_ROOT / cfg["training"]["output_dir"] / "final"
        if path.exists():
            tokenizer = AutoTokenizer.from_pretrained(str(path))
            model = AutoModelForSequenceClassification.from_pretrained(str(path))
            logger.info("Loaded fine-tuned checkpoint: %s", path)
        else:
            logger.warning("No checkpoint at %s — using base encoder (UNTRAINED head)", path)
            tokenizer, model = _load_base(cfg, num_labels=len(taxonomy_labels()))
        return cls(model, tokenizer, max_length=cfg["encoder"]["max_length"])

    @torch.no_grad()
    def predict(self, text: str) -> dict[str, float]:
        """Per-label sigmoid probabilities for one text."""
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=self.max_length
        ).to(self.device)
        logits = self.model(**inputs).logits
        probs = torch.sigmoid(logits)[0].cpu().numpy()
        return {label: float(probs[i]) for i, label in enumerate(self.labels)}


# ---------------------------------------------------------------- training


def _jsonl_to_dataset(path: Path, labels: list[str]):
    from datasets import Dataset

    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return Dataset.from_dict(
        {
            "text": [r["text"] for r in rows],
            "label_vector": [
                [float(r["distortions"].get(label, 0.0) >= 0.5) for label in labels] for r in rows
            ],
        }
    )


def train() -> None:
    from transformers import Trainer, TrainingArguments
    from sklearn.metrics import f1_score

    cfg = load_config("model")
    data_cfg = load_config("data")
    labels = taxonomy_labels()
    processed = PROJECT_ROOT / data_cfg["paths"]["processed_dir"]

    tokenizer, model = _load_base(cfg, num_labels=len(labels))

    def tokenize(batch):
        out = tokenizer(
            batch["text"], truncation=True, max_length=cfg["encoder"]["max_length"]
        )
        out["labels"] = [np.array(v, dtype=np.float32) for v in batch["label_vector"]]
        return out

    train_ds = _jsonl_to_dataset(processed / "train.jsonl", labels).map(tokenize, batched=True)
    val_ds = _jsonl_to_dataset(processed / "val.jsonl", labels).map(tokenize, batched=True)

    def compute_metrics(eval_pred):
        logits, gold = eval_pred
        preds = (1 / (1 + np.exp(-logits))) >= cfg["inference"]["decision_threshold"]
        return {
            "macro_f1": f1_score(gold, preds, average="macro", zero_division=0),
            "micro_f1": f1_score(gold, preds, average="micro", zero_division=0),
        }

    output_dir = PROJECT_ROOT / cfg["training"]["output_dir"]
    args = TrainingArguments(
        output_dir=str(output_dir),
        learning_rate=cfg["training"]["learning_rate"],
        per_device_train_batch_size=cfg["training"]["batch_size"],
        per_device_eval_batch_size=cfg["training"]["batch_size"],
        num_train_epochs=cfg["training"]["epochs"],
        weight_decay=cfg["training"]["weight_decay"],
        warmup_ratio=cfg["training"]["warmup_ratio"],
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=50,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    final_dir = output_dir / "final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    logger.info("Saved fine-tuned model -> %s", final_dir)
    logger.info("Eval: %s", trainer.evaluate())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train"])
    parser.parse_args()
    train()
