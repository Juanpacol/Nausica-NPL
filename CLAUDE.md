# Nausica — Cognitive Distortion & Reframing Trajectory System

## What this is
Detects cognitive distortions in text (5-type CBT taxonomy), aggregates them into a
continuous **Cognitive Flexibility Index (CFI)** — higher = more cognitively rigid —
and runs a Socratic reframing dialogue evaluated by whether CFI decreases across turns.
NOT a binary depression classifier. Research project for a graduate scholarship.

## Status
Phase 0 (foundation) + Phase 6 (web UI in `web/`) complete and pushed. Phase 2 in
progress: Obsidian plugin (`obsidian-plugin/`, built + smoke-tested), temporal CFI
transformer + contrastive rigidity embedding (training on synthetic dialogues).
Pending from Phase 1: full weak-labeling run + classifier fine-tune (classifier
head is currently UNTRAINED — API probabilities hover ~0.5).

## Architecture
- `src/data_pipeline/` — dataset download (ANGST, Mental Health Classification, Amod
  counseling), LLM weak labeling against the 5-type taxonomy, SMILE-style single→multi-turn
  dialogue expansion, preprocessing/splits.
- `src/models/` — `distortion_classifier.py` (MentalRoBERTa multi-label fine-tune),
  `mindset_profiler.py` (BERTopic, optional extra `clustering`),
  `reframing_dialogue.py` (pluggable `ReframingBackend`: `PromptBackend` default,
  `LoRABackend` optional/unimplemented until GPU confirmed).
- `src/metrics/cognitive_flexibility_index.py` — the novel continuous metric + per-session
  trajectory tracking. This is the paper's core contribution; treat changes carefully.
- `src/evaluation/` — `llm_judge.py` (mandatory rubric scoring), `clinical_review.py`
  (optional human-review hook, no-op without reviewers).
- `src/models/temporal_cfi.py` — small causal Transformer predicting the next-turn
  distortion vector from turn history (CFI derived via `compute_cfi`, single source
  of truth). Trained on SYNTHETIC dialogue trajectories — architecture validation,
  not clinical dynamics; must beat a persistence baseline or report the negative.
- `src/models/rigidity_embedding.py` — MiniLM fine-tuned contrastively on
  (rigid, flexible) client-turn pairs; `rigidity_score()` = projection onto the
  rigid→flexible centroid axis. Correlation vs classifier CFI = convergent-validity
  result (docs/VALIDATION.md).
- `src/api/main.py` — FastAPI: `POST /analyze`, `POST /reframe`,
  `GET /trajectory/{id}`, `POST /predict_trajectory`, `POST /rigidity_score`.
- `obsidian-plugin/` — "Nausica Cognitive Map" TypeScript plugin (local-first
  product surface): per-note clinical card + vault-wide rigidity map sidebar,
  cache in plugin data.json (NEVER writes into user notes). Test fixture:
  `demo-vault/` (synthetic journals — final visual check needs Obsidian desktop,
  not installed on this machine).
- `configs/*.yaml` — taxonomy/weights (`data.yaml`), encoder hyperparams (`model.yaml`),
  dialogue backend switch (`dialogue.yaml`).
- Docs: `docs/TAXONOMY.md` (label definitions), `docs/LICENSING.md` (verified license
  table — read before adding any external asset).

## Critical constraints
- `mental/mental-roberta-base` is **CC-BY-NC-4.0, gated** — non-commercial only. Never
  suggest commercial deployment without flagging re-licensing. Requires HF_TOKEN + accepted
  terms to download.
- All distortion labels are **LLM weak-labeled** (no clinician ground truth at scale).
  Always disclose this as a limitation; never claim clinical validity.
- Dialogue backend is pluggable — check `configs/dialogue.yaml` before assuming a
  fine-tuned model exists. `LoRABackend` is intentionally unimplemented (no GPU confirmed).
- This system is a research prototype, **not a medical device**. Outputs must never be
  framed as diagnosis or treatment.

## Reference repos (methodology only — none runnable in English)
SMILE (multi-turn expansion technique), Chinese-MentalBERT (domain-adaptive pretraining
template), CBT-LLM (5-type distortion taxonomy). I-HOPE / DepMamba / multimodal repos are
literature-review citations only. Verified details in `docs/LICENSING.md`.

## Conventions
- Python 3.10+, `pyproject.toml` (`pip install -e ".[dev]"`).
- Tests: `pytest` — pure-logic tests (CFI, preprocessing) must run without GPU, network,
  or API keys; anything needing the encoder/API is skipped via markers when unavailable.
- LLM calls go through `src/utils/llm_client.py` (provider-agnostic: default
  `ollama` = local qwen3:8b, free, no data leaves the machine; optional
  `anthropic`) — do not instantiate SDK/HTTP clients elsewhere. Provider set in
  configs/data.yaml `llm.provider` or env `NAUSICA_LLM_PROVIDER`.
- Config over code: taxonomy labels, CFI weights, model names live in `configs/`, not
  hardcoded.
- API keys only via `.env` (see `.env.example`); never committed, never logged.
