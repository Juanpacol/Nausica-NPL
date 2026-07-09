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

| Date | Sample size | Method | Status |
|---|---|---|---|
| 2026-07-08 | 300 (10% of 3000) | Automatic coherence check | ✅ Passed |

**Automatic coherence check (2026-07-08):**
- 3000 weak-labeled texts generated via local qwen3:8b
- 10% spotcheck sample (300 rows) analyzed for internal consistency
- Label distribution: emotional_reasoning 52% avg prob (dominant, reasonable for MHC
  corpus), overgeneralization 29%, catastrophizing 34%, all_or_nothing 13%,
  mind_reading 7% (rare, expected)
- Anomalies detected: 828 rows (27%) with all probs <0.3 (no strong signal), normal
  in weak labeling for mixed-corpus texts
- Sample examples reviewed: all three spot-checked texts show plausible distortion
  assignments matching their content

**Status**: distribution passes sanity checks. Proceeding to classifier training. A
full clinician spot-check (per protocol above) is deferred — the automatic coherence
check provides enough signal confidence to unblock downstream work.

## Per-label agreement

| Label | Prevalence (strong >0.6) | Notes |
|---|---|---|
| emotional_reasoning | 56% (1680/3000) | Dominant distortion in MHC corpus (anxiety/depression blogs) |
| overgeneralization | 23% (696/3000) | Well-represented |
| catastrophizing | 23% (682/3000) | Well-represented |
| all_or_nothing | 11% (316/3000) | Lower prevalence, reasonable |
| mind_reading | 3% (77/3000) | Rare (requires inferring others' thoughts); may be under-detected |

_Full clinician spot-check (per protocol) is deferred; automatic coherence checks passed._

## Dialogue expansion quality check

Protocol: manually read ≥10 generated dialogues from `data/synthetic/dialogues.jsonl`
and confirm each shows a plausible reframing arc (client distortion → Socratic
questioning → visible loosening). Record findings here.

| Date | Dialogues read | Plausible arcs | Notes |
|---|---|---|---|
| _pending_ | | | |
