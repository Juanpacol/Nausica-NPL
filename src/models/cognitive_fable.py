"""Cognitive Fable (Phase 8) — formalized, inspectable reframing policy.

Where PromptBackend alone lets the LLM freely decide how to respond (functionally
what CBT-LLM does), the Cognitive Fable makes the strategy an explicit, auditable
decision BEFORE any LLM call:

    FableState  (distortion profile + session turn)
        -> policy ->
    FableAction (CBT technique + target distortion + tone)

The action then CONSTRAINS the LLM's generation (see reframing_dialogue.py) instead
of being implicit in it. Two interchangeable policies, selected in
configs/model.yaml (`cognitive_fable.policy`):

- heuristic — deterministic config-driven rules (same philosophy as archetypes.py:
  clinicians tune the technique_map/severity_bands without retraining anything).
- learned   — FablePolicyNet, a small two-head MLP trained on (state, technique,
  tone) tuples extracted from the synthetic dialogues by an LLM annotator
  (src/data_pipeline/build_fable_policy_dataset.py). Same weak-label pattern and
  the same honesty caveat as temporal_cfi.py: it validates the policy
  architecture, not clinical optimality. Falls back to the heuristic when the
  checkpoint is missing.

Train: python -m src.models.cognitive_fable train
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from src.utils.config import PROJECT_ROOT, load_config, taxonomy_labels
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class FableState:
    """Everything the policy sees before choosing a counselor strategy."""

    distortions: dict[str, float]
    session_turn: int = 1


@dataclass(frozen=True)
class FableAction:
    """The chosen strategy — rendered into LLM constraints, and logged/auditable."""

    technique: str
    target_distortion: str
    tone: str


# ------------------------------------------------------------ heuristic policy


def default_policy(state: FableState) -> FableAction:
    """Deterministic config-driven policy (configs/model.yaml `cognitive_fable`).

    Strongest detected distortion picks the technique via technique_map; its
    severity picks the tone via severity_bands (first matching band wins).
    Ties break by taxonomy order for determinism. Empty/zero profiles get the
    fallback technique with the lowest-severity tone.
    """
    cfg = load_config("model")["cognitive_fable"]
    labels = taxonomy_labels()

    known = {k: v for k, v in state.distortions.items() if k in labels}
    if not known or max(known.values()) <= 0.0:
        return FableAction(
            technique=cfg["fallback_technique"],
            target_distortion="none",
            tone=cfg["severity_bands"][-1]["tone"],
        )

    strongest = max(known, key=lambda k: (known[k], -labels.index(k)))
    prob = known[strongest]
    technique = cfg["technique_map"].get(strongest, cfg["fallback_technique"])
    tone = next(
        band["tone"] for band in cfg["severity_bands"] if prob >= band["min_prob"]
    )
    return FableAction(technique=technique, target_distortion=strongest, tone=tone)


# ------------------------------------------------------------- learned policy


class FablePolicyNet:
    """Small two-head MLP: (5 distortion probs + normalized turn) -> technique, tone.

    Deliberately tiny — the training set is a few hundred LLM-annotated turns from
    synthetic dialogues. Lazy torch import keeps the heuristic path dependency-free.
    """

    MAX_TURN_NORM = 16.0  # session turns beyond this all look "late" to the net

    def __init__(self, model, techniques: list[str], tones: list[str]):
        self.model = model
        self.techniques = techniques
        self.tones = tones

    @staticmethod
    def _build(n_in: int, hidden: int, n_tech: int, n_tone: int):
        import torch
        from torch import nn

        class _Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.trunk = nn.Sequential(nn.Linear(n_in, hidden), nn.ReLU())
                self.tech_head = nn.Linear(hidden, n_tech)
                self.tone_head = nn.Linear(hidden, n_tone)

            def forward(self, x: torch.Tensor):
                h = self.trunk(x)
                return self.tech_head(h), self.tone_head(h)

        return _Net()

    def _featurize(self, state: FableState):
        import torch

        labels = taxonomy_labels()
        feats = [state.distortions.get(label, 0.0) for label in labels]
        feats.append(min(state.session_turn, self.MAX_TURN_NORM) / self.MAX_TURN_NORM)
        return torch.tensor([feats], dtype=torch.float32)

    def predict(self, state: FableState) -> FableAction:
        import torch

        self.model.eval()
        with torch.no_grad():
            tech_logits, tone_logits = self.model(self._featurize(state))
        technique = self.techniques[int(tech_logits.argmax())]
        tone = self.tones[int(tone_logits.argmax())]
        labels = taxonomy_labels()
        known = {k: v for k, v in state.distortions.items() if k in labels}
        target = max(known, key=known.get) if known and max(known.values()) > 0 else "none"
        return FableAction(technique=technique, target_distortion=target, tone=tone)

    # -------------------------------------------------------------- persistence

    @classmethod
    def load(cls, path: str | Path | None = None) -> "FablePolicyNet":
        import torch

        cfg = load_config("model")["cognitive_fable"]
        ckpt_path = Path(path) if path else PROJECT_ROOT / cfg["checkpoint"]
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
        model = cls._build(**ckpt["arch"])
        model.load_state_dict(ckpt["state_dict"])
        model.eval()
        return cls(model, techniques=ckpt["techniques"], tones=ckpt["tones"])

    def save(self, path: Path, arch: dict) -> None:
        import torch

        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "arch": arch,
                "state_dict": self.model.state_dict(),
                "techniques": self.techniques,
                "tones": self.tones,
            },
            path,
        )


# --------------------------------------------------------------- the Fable


class CognitiveFable:
    """Policy dispatcher: configs/model.yaml `cognitive_fable.policy` selects
    heuristic vs learned; learned degrades to heuristic if untrained (same
    fallback philosophy as the classifier's untrained-head path)."""

    def __init__(self, policy: str | None = None):
        cfg = load_config("model")["cognitive_fable"]
        self.policy_name = policy or cfg["policy"]
        self._net: FablePolicyNet | None = None
        if self.policy_name == "learned":
            try:
                self._net = FablePolicyNet.load()
                logger.info("CognitiveFable: learned policy loaded")
            except FileNotFoundError:
                logger.warning(
                    "CognitiveFable: no checkpoint at %s — falling back to heuristic "
                    "(train with: python -m src.models.cognitive_fable train)",
                    cfg["checkpoint"],
                )
                self.policy_name = "heuristic"
        elif self.policy_name != "heuristic":
            raise ValueError(
                f"Unknown cognitive_fable.policy {self.policy_name!r} (heuristic|learned)"
            )

    def select_action(self, state: FableState) -> FableAction:
        if self._net is not None:
            return self._net.predict(state)
        return default_policy(state)


# ------------------------------------------------------------------- training


def train() -> None:
    """Fit FablePolicyNet on data/processed/fable_policy_dataset.jsonl and report
    held-out accuracy vs the heuristic baseline — win or lose (VALIDATION.md)."""
    import torch
    from torch import nn

    cfg = load_config("model")["cognitive_fable"]
    tcfg = cfg["training"]
    labels = taxonomy_labels()
    techniques, tones = cfg["techniques"], cfg["tones"]

    data_path = (
        PROJECT_ROOT / load_config("data")["paths"]["processed_dir"] / "fable_policy_dataset.jsonl"
    )
    rows = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]
    rows = [r for r in rows if r["technique"] in techniques and r["tone"] in tones]
    if len(rows) < 20:
        raise SystemExit(f"Only {len(rows)} usable rows in {data_path} — need at least 20")

    rng = random.Random(tcfg["seed"])
    rng.shuffle(rows)
    n_val = max(1, int(len(rows) * tcfg["val_fraction"]))
    val_rows, train_rows = rows[:n_val], rows[n_val:]
    logger.info("FablePolicyNet: %d train / %d val rows", len(train_rows), len(val_rows))

    def to_tensors(subset):
        x = torch.tensor(
            [
                [r["distortions"].get(label, 0.0) for label in labels]
                + [min(r["session_turn"], FablePolicyNet.MAX_TURN_NORM) / FablePolicyNet.MAX_TURN_NORM]
                for r in subset
            ],
            dtype=torch.float32,
        )
        y_tech = torch.tensor([techniques.index(r["technique"]) for r in subset])
        y_tone = torch.tensor([tones.index(r["tone"]) for r in subset])
        return x, y_tech, y_tone

    x_tr, yt_tr, yo_tr = to_tensors(train_rows)
    x_va, yt_va, yo_va = to_tensors(val_rows)

    arch = {
        "n_in": len(labels) + 1,
        "hidden": tcfg["hidden_dim"],
        "n_tech": len(techniques),
        "n_tone": len(tones),
    }
    torch.manual_seed(tcfg["seed"])
    model = FablePolicyNet._build(**arch)
    optim = torch.optim.Adam(model.parameters(), lr=tcfg["learning_rate"])
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(tcfg["epochs"]):
        model.train()
        optim.zero_grad()
        tech_logits, tone_logits = model(x_tr)
        loss = loss_fn(tech_logits, yt_tr) + loss_fn(tone_logits, yo_tr)
        loss.backward()
        optim.step()
        if (epoch + 1) % 50 == 0:
            logger.info("epoch %d loss %.4f", epoch + 1, float(loss))

    # ------------------------------------------------------------- evaluation
    model.eval()
    with torch.no_grad():
        tech_logits, tone_logits = model(x_va)
    net_tech_acc = float((tech_logits.argmax(1) == yt_va).float().mean())
    net_tone_acc = float((tone_logits.argmax(1) == yo_va).float().mean())

    # Honest baseline: what would the heuristic have chosen on the same rows?
    heur_tech_hits = heur_tone_hits = 0
    for r in val_rows:
        act = default_policy(FableState(distortions=r["distortions"], session_turn=r["session_turn"]))
        heur_tech_hits += act.technique == r["technique"]
        heur_tone_hits += act.tone == r["tone"]
    heur_tech_acc = heur_tech_hits / len(val_rows)
    heur_tone_acc = heur_tone_hits / len(val_rows)

    net = FablePolicyNet(model, techniques=techniques, tones=tones)
    ckpt_path = PROJECT_ROOT / cfg["checkpoint"]
    net.save(ckpt_path, arch)

    metrics = {
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "net_technique_acc": round(net_tech_acc, 4),
        "net_tone_acc": round(net_tone_acc, 4),
        "heuristic_technique_acc": round(heur_tech_acc, 4),
        "heuristic_tone_acc": round(heur_tone_acc, 4),
        "trained_on": "synthetic LLM-annotated dialogues (see VALIDATION.md caveat)",
    }
    (ckpt_path.parent / "metrics.json").write_text(json.dumps(metrics, indent=2))
    logger.info("Saved %s | %s", ckpt_path, metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train"])
    parser.parse_args()
    train()
