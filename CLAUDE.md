# Nausica — Cognitive Distortion & Reframing Trajectory System

## What this is
Detects cognitive distortions in text (5-type CBT taxonomy), aggregates them into a
continuous **Cognitive Flexibility Index (CFI)** — higher = more cognitively rigid —
and runs a Socratic reframing dialogue evaluated by whether CFI decreases across turns.
NOT a binary depression classifier. Research project for a graduate scholarship.

## Status
Complete through Phase 7 product roadmap: foundation, web UI (`web/`), Obsidian
plugin, temporal transformer + rigidity embedding (Phase 2), PostgreSQL + JWT auth
(Phase 3), archetypes/composite score/PDF reports (Phase 4), clinician dashboard +
consent (Phase 5), RAG reframing + voice ingestion (Phase 6), clinician-feedback
capture + DPO export (Phase 7). Pending from Phase 1: full weak-labeling run +
classifier fine-tune (classifier head is currently UNTRAINED — probabilities ~0.5,
which flattens temporal dynamics; see docs/VALIDATION.md).

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
- `src/db/` + `alembic/` — SQLAlchemy models (User/Organization/OrgMembership/
  Session/Turn/NoteAnalysis) on PostgreSQL; sessions persist across restarts.
  Local dev: Homebrew postgresql@18, db `nausica`; portable: docker-compose.yml
  (pgvector/pgvector image, ready for the pgvector scale-up path). Migrations via
  Alembic (`alembic upgrade head`). Tests use in-memory SQLite (tests/conftest.py).
- `src/auth/` — JWT (python-jose) + bcrypt passwords. ALL data endpoints require
  Bearer token. `require_clinician_of` enforces: shared org + clinician/admin role
  + the patient's explicit `consent_clinician_view` (opt-in, default False,
  revocable). Set NAUSICA_JWT_SECRET in prod.
- `src/models/archetypes.py` — config-driven distortion-combo → archetype mapping
  (configs/model.yaml `archetypes`); deliberately rule-based so clinicians can tune
  it without retraining.
- `src/models/cognitive_fable.py` — formalized reframing policy (Phase 8):
  FableState (distortions + turn) → FableAction (CBT technique + tone) decided
  BEFORE the LLM call and injected as generation constraints (differentiator vs
  prompt-only systems; spec: docs/FABLE_SPECIFICATION.md). Two policies via
  configs/model.yaml `cognitive_fable.policy`: `heuristic` (config rules, like
  archetypes) | `learned` (FablePolicyNet MLP on LLM-annotated synthetic
  dialogues via `build_fable_policy_dataset.py`; falls back to heuristic if
  untrained). NOT the same thing as Claude Fable, the Anthropic model.
- `src/metrics/composite_rigidity.py` — weighted blend of the 3 rigidity signals;
  weights are HEURISTIC (configs/model.yaml), renormalizes over available signals,
  `signal_spread` flags disagreement instead of hiding it.
- `src/reports/builder.py` — clinical PDF via matplotlib PdfPages (weasyprint
  needs GTK native libs, absent here). Renders derived scores only — never raw
  client text; disclaimer on every page.
- `src/models/rag_retrieval.py` — RAG for reframing: retrieves the user's OWN past
  exchanges where the counselor reply measurably lowered CFI (cosine over JSON
  embeddings; pgvector is the documented scale-up). No cross-user leakage.
- `scripts/export_preference_pairs.py` — clinician feedback → DPO-format JSONL.
  Capture only; no training here.
- `src/api/main.py` — FastAPI: `/auth/*`, `POST /analyze`, `POST /analyze/audio`
  (faster-whisper, local), `POST /reframe` (RAG-augmented), `GET /trajectory/{id}`,
  `POST /predict_trajectory`, `POST /rigidity_score`, `POST /composite_rigidity`,
  `GET /profile/archetype`, `GET|POST /profile/consent`, `GET /org/patients`,
  `GET /reports/{user_id}.pdf`, `POST /turns/{id}/feedback`.
- `obsidian-plugin/` — "Nausica Cognitive Map" TypeScript plugin (local-first
  product surface): per-note clinical card + vault-wide rigidity map sidebar,
  cache in plugin data.json (NEVER writes into user notes). Test fixture:
  `demo-vault/` (synthetic journals — final visual check needs Obsidian desktop,
  not installed on this machine).
- `configs/*.yaml` — taxonomy/weights (`data.yaml`), encoder hyperparams (`model.yaml`),
  dialogue backend switch (`dialogue.yaml`).
- Docs: `docs/TAXONOMY.md` (label definitions), `docs/LICENSING.md` (verified license
  table — read before adding any external asset), `docs/ARCHITECTURE.md` (data-flow
  diagram + future-work register), `docs/CFI_SPECIFICATION.md` and
  `docs/FABLE_SPECIFICATION.md` (formal specs for the two core contributions),
  `docs/VALIDATION.md` (honest training results), `docs/DATA_QUALITY.md`
  (weak-label spot-check evidence).

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
- LLM calls go through `src/utils/llm_client.py` (provider-agnostic) — do not
  instantiate SDK/HTTP clients elsewhere. Provider is set PER TASK in configs
  (`llm.provider` global default plus `provider:` keys in `prompt_backend`,
  `dialogue_expansion`, `judge`). Current posture: ALL tasks local-first
  (`ollama`/qwen3:8b, free, no key, no data leaves the machine). Documented
  upgrade path: switch generation/evaluation tasks to `anthropic`/claude-fable-5
  when budget allows — flag that those texts then leave the machine. Global
  fallback overridable via env `NAUSICA_LLM_PROVIDER`.
- Config over code: taxonomy labels, CFI weights, model names live in `configs/`, not
  hardcoded.
- API keys only via `.env` (see `.env.example`); never committed, never logged.
