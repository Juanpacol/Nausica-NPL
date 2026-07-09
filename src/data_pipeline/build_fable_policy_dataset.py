"""Build the (state, action) dataset for FablePolicyNet (Phase 8).

Walks the SMILE-style synthetic dialogues (data/synthetic/dialogues.jsonl) and, for
every counselor turn that follows a client turn, produces one training row:

    state  — distortion vector of the preceding client turn (DistortionClassifier)
             + the session turn index
    action — which CBT technique/tone the counselor turn actually used, annotated
             retrospectively by an LLM (provider/model from configs/data.yaml
             `dialogue_expansion` — same tier as the dialogue generator)

Output: data/processed/fable_policy_dataset.jsonl with rows
    {"distortions": {label: prob}, "session_turn": int, "technique": str, "tone": str}

LIMITATION (disclose, same pattern as weak labeling / temporal): both the dialogues
and the technique annotations are synthetic/LLM-derived. A policy trained on them
validates the architecture, not clinical optimality.

Usage: python -m src.data_pipeline.build_fable_policy_dataset [--limit N]
"""

from __future__ import annotations

import argparse
import json

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.llm_client import LLMClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

ANNOTATOR_SYSTEM = """You are an expert CBT supervisor. Classify which reframing \
technique a counselor's turn uses, and its tone. Choose exactly one of each.

techniques:
- downward_arrow — probes what a feared outcome would mean, digging toward the core belief
- evidence_exam — asks for evidence, counter-examples, or exceptions to a belief
- behavioral_exp — proposes checking an assumption against reality (asking, observing, testing)
- spectrum — invites gradations between all-or-nothing extremes, partial successes
- socratic — general open exploratory questioning not fitting the above

tones:
- validating — leads with warmth/acknowledgement of the feeling before any question
- gently_challenging — respectfully questions the belief itself
- exploratory — neutral curiosity, open-ended

Respond ONLY with JSON: {"technique": "...", "tone": "..."}"""


def annotate_turn(client: LLMClient, client_text: str, counselor_text: str,
                  techniques: list[str], tones: list[str]) -> dict[str, str]:
    """LLM-annotate one counselor turn; validates against the config vocab."""
    prompt = f"[client]: {client_text}\n[counselor]: {counselor_text}"
    raw = client.complete_json(prompt, system=ANNOTATOR_SYSTEM)
    if not isinstance(raw, dict) or raw.get("technique") not in techniques or raw.get("tone") not in tones:
        raise ValueError(f"Bad annotation: {raw!r}")
    return {"technique": raw["technique"], "tone": raw["tone"]}


def run(limit: int | None = None) -> None:
    from src.models.distortion_classifier import DistortionClassifier

    data_cfg = load_config("data")
    fable_cfg = load_config("model")["cognitive_fable"]
    in_path = PROJECT_ROOT / data_cfg["paths"]["synthetic_dir"] / "dialogues.jsonl"
    out_path = PROJECT_ROOT / data_cfg["paths"]["processed_dir"] / "fable_policy_dataset.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dialogues = [json.loads(line) for line in in_path.read_text().splitlines() if line.strip()]
    if limit:
        dialogues = dialogues[:limit]
    logger.info("Building fable policy rows from %d dialogues", len(dialogues))

    ann_cfg = data_cfg["dialogue_expansion"]  # same provider tier as generation
    llm = LLMClient(model=ann_cfg["model"], max_tokens=256, provider=ann_cfg.get("provider"))
    classifier = DistortionClassifier.load()

    written = 0
    with open(out_path, "w") as out:
        for d in dialogues:
            turns = d["turns"]
            client_turn_idx = 0
            for i, turn in enumerate(turns):
                if turn["role"] == "client":
                    client_turn_idx += 1
                    continue
                if i == 0 or turns[i - 1]["role"] != "client":
                    continue  # counselor turn without an immediately preceding client turn
                client_text = turns[i - 1]["text"]
                try:
                    action = annotate_turn(
                        llm, client_text, turn["text"],
                        fable_cfg["techniques"], fable_cfg["tones"],
                    )
                except Exception as e:  # noqa: BLE001 — skip bad rows, keep the run alive
                    logger.warning("dialogue %s turn %d failed: %s", d.get("source_index"), i, e)
                    continue
                out.write(json.dumps({
                    "distortions": classifier.predict(client_text),
                    "session_turn": client_turn_idx,
                    **action,
                }) + "\n")
                written += 1
            if written and written % 25 == 0:
                logger.info("  %d rows — %s", written, llm.usage_summary())

    logger.info("Done: %d rows -> %s | %s", written, out_path, llm.usage_summary())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap dialogues (cheap dry runs)")
    args = parser.parse_args()
    run(args.limit)
