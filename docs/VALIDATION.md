# Validation Results — Phase 2 (Temporal Dynamics + Rigidity Embedding)

Honest, unfiltered results from the first end-to-end training runs (2026-07-06).
Everything below trains on **synthetic data** (49 LLM-generated dialogues via local
qwen3:8b, ~4 client turns each) and the distortion classifier head was **untrained**
at the time of these runs — both caveats propagate into every number here. These
runs validate the *architecture and pipeline*, not clinical dynamics.

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
| Pearson r vs classifier CFI (98 texts) | 0.705 (p < 0.0001) |

**Honest reading:** the base MiniLM already orders every val pair correctly —
a ceiling effect: with only 9 val pairs and synthetic reformulations that differ
strongly in surface form, the task is too easy to show fine-tuning gains. The
r = 0.705 correlation with the classifier CFI is a promising convergent-validity
signal but carries the untrained-classifier caveat (`classifier_untrained: true`
in metrics.json) and must be recomputed after the fine-tune.

Qualitative sanity check (live API, texts never seen in training):
- "I always ruin everything and nobody will ever love me." → rigidity 0.349
- "Today was hard, but maybe I can learn something…" → rigidity 0.096

The embedding separates rigid from flexible framings on unseen inputs in the
expected direction.

## 3. What must happen before these numbers are paper-ready

1. Fine-tune the distortion classifier (Phase 1 weak labeling at scale) — unblocks
   real temporal dynamics and a meaningful CFI correlation.
2. Scale synthetic dialogues (≥300) and/or collect real longitudinal journaling
   data (the Obsidian plugin is the collection instrument).
3. Larger val splits; report confidence intervals.
4. Human spot-check of dialogue reframing arcs (protocol in docs/DATA_QUALITY.md).
