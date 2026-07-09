"""SMILE-style single-turn -> multi-turn dialogue expansion, in English.

Reproduces the technique from SMILE (arXiv:2305.00450) — prompt an LLM to rewrite a
single counseling Q&A pair into a realistic 5-7 turn dialogue — with one addition:
the generated dialogue must show a *reframing arc* (client voices a distorted belief,
counselor questions Socratically, the client's framing visibly loosens by the end).
These synthetic dialogues are the training/eval material for the reframing module.

Usage:
    python -m src.data_pipeline.dialogue_expansion --limit 50
Reads the Amod counseling dataset from data/raw/, writes data/synthetic/dialogues.jsonl
"""

from __future__ import annotations

import argparse
import json

from datasets import load_from_disk

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.llm_client import LLMClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You expand single-turn counseling Q&A pairs into realistic multi-turn \
counseling dialogues, following CBT practice. Requirements:
- {min_turns} to {max_turns} total turns, alternating "client" / "counselor", starting with client.
- The client's opening turn must express the same core concern as the original question, \
including any cognitive distortion present in it.
- The counselor uses Socratic questioning (open questions, evidence examination, \
downward arrow) — never lectures, never gives direct advice in the first turns.
- Across the dialogue the client's framing should gradually loosen: the final client turn \
shows a small but genuine shift (more nuance, less absolutism) — realistic, not miraculous.
- Natural conversational English. No stage directions, no numbered lists inside turns.

Respond ONLY with a JSON object of this exact shape:
{{"turns": [{{"role": "client", "text": "..."}}, {{"role": "counselor", "text": "..."}}, ...]}}"""


def expand_pair(client: LLMClient, question: str, answer: str,
                min_turns: int, max_turns: int) -> list[dict]:
    system = SYSTEM_PROMPT.format(min_turns=min_turns, max_turns=max_turns)
    prompt = (
        f"Original client question:\n{question}\n\n"
        f"Original counselor answer (use as grounding for the counselor's approach):\n{answer}"
    )
    raw = client.complete_json(prompt, system=system)
    turns = raw.get("turns") if isinstance(raw, dict) else raw
    if not isinstance(turns, list) or len(turns) < min_turns:
        n = len(turns) if isinstance(turns, list) else type(raw)
        raise ValueError(f"Bad expansion: {n} turns")
    for t in turns:
        if t.get("role") not in ("client", "counselor") or not t.get("text"):
            raise ValueError(f"Malformed turn: {t}")
    return turns


def run(limit: int | None = None) -> None:
    cfg = load_config("data")
    exp_cfg = cfg["dialogue_expansion"]
    raw_dir = PROJECT_ROOT / cfg["datasets"]["counseling_conversations"]["local_dir"]
    out_path = PROJECT_ROOT / cfg["paths"]["synthetic_dir"] / "dialogues.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ds = load_from_disk(str(raw_dir))["train"]
    if limit:
        ds = ds.select(range(min(limit, len(ds))))
    logger.info("Expanding %d single-turn pairs into multi-turn dialogues", len(ds))

    llm = LLMClient(model=exp_cfg["model"], max_tokens=4096, provider=exp_cfg.get("provider"))
    written = 0
    with open(out_path, "w") as out:
        for i, row in enumerate(ds):
            question = row.get("Context") or row.get("questionText") or ""
            answer = row.get("Response") or row.get("answerText") or ""
            if not question.strip() or not answer.strip():
                continue
            try:
                turns = expand_pair(llm, question, answer,
                                    exp_cfg["min_turns"], exp_cfg["max_turns"])
            except Exception as e:  # noqa: BLE001 — skip bad rows, keep the run alive
                logger.warning("row %d failed: %s", i, e)
                continue
            out.write(json.dumps({"source_index": i, "turns": turns}) + "\n")
            written += 1
            if written % 25 == 0:
                logger.info("  %d dialogues written — %s", written, llm.usage_summary())

    logger.info("Done: %d dialogues -> %s | %s", written, out_path, llm.usage_summary())
    logger.info("REMINDER: manually read >=10 dialogues to confirm plausible reframing arcs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap rows (for cheap dry runs)")
    args = parser.parse_args()
    run(args.limit)
