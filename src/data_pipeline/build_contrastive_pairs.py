"""Build (rigid, flexible) text pairs for the contrastive rigidity embedding
(Phase 2, pillar 3).

The SMILE-style synthetic dialogues are generated with an explicit reframing arc:
the client's FIRST turn expresses the distorted/rigid framing and the LAST client
turn shows a loosened, more flexible reformulation of the same concern. That
structural guarantee is what makes the pair extraction valid:

    {"rigid": <first client turn>, "flexible": <last client turn>, "dialogue_index": int}

LIMITATION (disclose): pair quality inherits from the generation model; pairs are
synthetic reformulations, not clinician-authored reframes.

Usage: python -m src.data_pipeline.build_contrastive_pairs
"""

from __future__ import annotations

import argparse
import json

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

MIN_CHARS = 25  # drop degenerate turns ("ok", "thanks") that carry no framing


def run(limit: int | None = None) -> None:
    cfg = load_config("data")
    in_path = PROJECT_ROOT / cfg["paths"]["synthetic_dir"] / "dialogues.jsonl"
    out_path = PROJECT_ROOT / cfg["paths"]["processed_dir"] / "contrastive_pairs.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dialogues = [json.loads(line) for line in in_path.read_text().splitlines() if line.strip()]
    if limit:
        dialogues = dialogues[:limit]

    written = 0
    with open(out_path, "w") as out:
        for d in dialogues:
            client_turns = [t["text"].strip() for t in d["turns"] if t["role"] == "client"]
            if len(client_turns) < 2:
                continue
            rigid, flexible = client_turns[0], client_turns[-1]
            if len(rigid) < MIN_CHARS or len(flexible) < MIN_CHARS or rigid == flexible:
                continue
            out.write(
                json.dumps(
                    {
                        "rigid": rigid,
                        "flexible": flexible,
                        "dialogue_index": d.get("source_index", written),
                    }
                )
                + "\n"
            )
            written += 1

    logger.info("Done: %d contrastive pairs -> %s", written, out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.limit)
