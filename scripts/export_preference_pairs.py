"""Export clinician feedback as DPO preference pairs (Phase 7).

Reads counselor turns that carry clinician feedback (POST /turns/{id}/feedback)
and writes JSONL in the standard DPO format:

    {"prompt": <client text + context>, "chosen": <good reframe>, "rejected": <bad reframe>}

Pair construction:
- feedback_good=True  -> the counselor turn is a `chosen` candidate
- feedback_good=False + correction_text -> (correction=chosen, original=rejected)
  for the same prompt — the strongest signal, a direct clinician rewrite.
- feedback_good=False without correction is logged and skipped (no chosen side).

NOTHING is trained here — this only accumulates data until there is enough
volume for a separate DPO fine-tuning project (see CLAUDE.md roadmap).

Usage: python -m scripts.export_preference_pairs [--out data/processed/preference_pairs.jsonl]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.db.models import Turn
from src.db.session import get_sessionmaker
from src.utils.config import PROJECT_ROOT
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _prompt_for(db, turn: Turn) -> str | None:
    """The client turn immediately preceding this counselor turn."""
    prev = (
        db.query(Turn)
        .filter_by(session_id=turn.session_id, turn_idx=turn.turn_idx - 1, role="client")
        .first()
    )
    return prev.text if prev else None


def run(out_path: Path) -> int:
    db = get_sessionmaker()()
    try:
        reviewed = (
            db.query(Turn)
            .filter(Turn.role == "counselor", Turn.clinician_feedback_good.isnot(None))
            .order_by(Turn.created_at)
            .all()
        )
        logger.info("Counselor turns with feedback: %d", len(reviewed))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        written = skipped = 0
        with open(out_path, "w") as out:
            for turn in reviewed:
                prompt = _prompt_for(db, turn)
                if prompt is None:
                    skipped += 1
                    continue
                if turn.clinician_feedback_good is False and turn.clinician_feedback_text:
                    out.write(json.dumps({
                        "prompt": prompt,
                        "chosen": turn.clinician_feedback_text,
                        "rejected": turn.text,
                        "source": "clinician_correction",
                    }) + "\n")
                    written += 1
                elif turn.clinician_feedback_good is False:
                    skipped += 1  # rejected with no correction — no chosen side
                # good_reframe=True alone yields no pair yet; it needs a rejected
                # counterpart. Kept in DB for future pairing strategies.

        logger.info("Wrote %d preference pairs -> %s (%d skipped)", written, out_path, skipped)
        return written
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "preference_pairs.jsonl",
    )
    args = parser.parse_args()
    run(args.out)
