# Validation Results — Phase 2 (Temporal Dynamics + Rigidity Embedding)

Honest, unfiltered results. Phase 1 runs (2026-07-08): classifier fine-tuned on
3000 weak-labeled texts. Everything below trains on **synthetic data** (49
LLM-generated dialogues via local qwen3:8b, ~4 client turns each) — the classifier
caveats are lifted, but the dialogue volume is still small and data is LLM-synthetic,
not clinical. These runs validate the *architecture and pipeline*, not clinical
dynamics.

## 1. Temporal CFI Transformer (`src/models/temporal_cfi.py`)

Setup: 2-layer causal Transformer (d_model=32), predicts next-turn distortion
vector; 40 train / 9 val dialogues (session-level split); baseline = persistence
(next = last observed). Metrics: `results/temporal_cfi/metrics.json`.

| Metric | Model | Persistence baseline |
|---|---|---|
| MAE (next-turn distortion vector) | 0.00172 | **0.00171** |
| Direction accuracy (±0.02 tolerance) | **0.637** | 0.0 |

**Honest reading:** the model does NOT beat persistence on MAE — they are tied,
because the underlying sequences are nearly flat: with the classifier head
untrained, every turn's distortion vector sits at ~0.5, so there is almost no
dynamics to learn (sample val CFI trajectory: 0.4995 → 0.4998 → 0.4997 → 0.5004).
Direction accuracy favors the model only because persistence predicts exactly zero
change. **Conclusion: pipeline works end-to-end; meaningful evaluation is blocked
on the Phase 1 classifier fine-tune.** Re-run this training after the classifier
lands and update this table.

## 2. Contrastive Rigidity Embedding (`src/models/rigidity_embedding.py`)

Setup: MiniLM-L6-v2 fine-tuned with MultipleNegativesRankingLoss on 40 (rigid,
flexible) pairs; scored by projection onto the rigid→flexible centroid axis;
9 held-out val pairs. Metrics: `results/rigidity_embedding/metrics.json`.

| Metric | Value |
|---|---|
| Held-out ordering accuracy (fine-tuned) | 1.00 |
| Held-out ordering accuracy (base model, no fine-tune) | 1.00 |
| Pearson r vs classifier CFI (98 texts) | 0.474 (p < 0.0001) |

**Honest reading:** the base MiniLM still orders every val pair correctly (ceiling
effect: 9 val pairs on synthetic reformulations). The r = 0.474 correlation with
the now-trained classifier CFI shows convergent validity is weaker than the
earlier untrained-classifier read (r = 0.705), which was inflated by the
classifier flatness. The true correlation is moderate — suggests that the
rigidity embedding is measuring a different axis than CFI (reasonable: rigidity
axis is learned from semantic pairs, CFI is computed from distortion probs).

Qualitative sanity check (live API, texts never seen in training):
- "I always ruin everything and nobody will ever love me." → rigidity 0.349
- "Today was hard, but maybe I can learn something…" → rigidity 0.096

The embedding separates rigid from flexible framings on unseen inputs in the
expected direction.

## 2b. Composite Rigidity Score (Phase 4 — heuristic, NOT calibrated)

`src/metrics/composite_rigidity.py` blends the three signals with weights from
configs/model.yaml (0.5 classifier CFI / 0.25 temporal / 0.25 embedding). These
weights are a HEURISTIC starting point — there is no real outcome data to
calibrate them against yet. The `signal_spread` field reports max−min across
signals so disagreement is visible rather than averaged away. Recalibrate by
regression once real longitudinal data exists.

Live e2e check (2026-07-07): all three signals active, composite 0.43 on a
rigid probe text with spread 0.30 — the spread being large is expected while the
classifier head is untrained.

## 3. What must happen before these numbers are paper-ready

1. ✅ **DONE** Fine-tune the distortion classifier (Phase 1 weak labeling on 3000
   texts via qwen3:8b) — unblocks real temporal dynamics and meaningful CFI signals.
2. Scale synthetic dialogues (≥300, regenerate with better LLM if budget allows)
   and/or collect real longitudinal journaling data (the Obsidian plugin is the
   collection instrument).
3. With trained classifier on real dialogue volume, re-run temporal_cfi training and
   report whether it beats persistence (current: MAE tie @ 0.00172).
4. Larger val splits; report confidence intervals.
5. Human spot-check of dialogue reframing arcs (protocol in docs/DATA_QUALITY.md).
