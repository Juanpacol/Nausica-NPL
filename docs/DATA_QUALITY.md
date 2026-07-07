# Data Quality Log

Records the mandatory human spot-check of LLM weak labels (Phase 1) and any other
data-quality observations. This file is the evidence base for the "weak labeling"
limitation section of the paper.

## Weak-label spot-check protocol

1. `weak_labeling.py` automatically writes a 10% random sample to
   `data/processed/weak_labeled_spotcheck.jsonl`.
2. A human reviews each sampled text against `docs/TAXONOMY.md` definitions and marks
   each assigned label as correct / incorrect / borderline.
3. Record the agreement rate below. If per-label agreement < 80%, revise the few-shot
   prompt in `weak_labeling.py` and re-run before training the classifier.

## Results

| Date | Sample size | Overall agreement | Notes |
|---|---|---|---|
| _pending — fill after first weak-labeling run_ | | | |

## Per-label agreement

| Label | Agreement | Common failure mode |
|---|---|---|
| all_or_nothing | _pending_ | |
| overgeneralization | _pending_ | |
| emotional_reasoning | _pending_ | |
| catastrophizing | _pending_ | |
| mind_reading | _pending_ | |

## Dialogue expansion quality check

Protocol: manually read ≥10 generated dialogues from `data/synthetic/dialogues.jsonl`
and confirm each shows a plausible reframing arc (client distortion → Socratic
questioning → visible loosening). Record findings here.

| Date | Dialogues read | Plausible arcs | Notes |
|---|---|---|---|
| _pending_ | | | |
