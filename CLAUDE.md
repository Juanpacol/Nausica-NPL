# Nausica — Neuro-Symbolic Clinical Reasoning Architecture

## What this is

**Research Project (Doctoral Level):** A neuro-symbolic architecture for interpretable
clinical decision support, instantiated on OCD via real-time cognitive distortion detection
and evidence-based CBT recommendation.

**Core Innovation:** Integrate LLM flexibility + Neural network prediction + Knowledge Graph
reasoning + Symbolic rule verification into a single pipeline. Each layer has a specific job;
none operates as a black box.

**Why it matters:** LLMs are opaque in clinical settings. This architecture makes reasoning
explicit, verifiable, and clinically defensible—while preserving the nuance that neural models
provide.

**Not this:** A depression classifier, a therapy chatbot, a replacement for human clinicians.

**Exactly this:** A research methodology that can be instantiated on any clinical domain where
interpretability matters (psychiatry, oncology, primary care, etc.).

See `docs/RESEARCH_PROPOSAL.md` for the full research plan (Doctoral proposal, 6 research
questions, 4-year roadmap, expected publications).

## Status (Current Work)

**Phase 1 (COMPLETE):** Infrastructure + Distortion Classifier Training
- Weak-labeled 3000 texts (OCD + anxiety corpus)
- Trained DistortionClassifier (RoBERTa fine-tuned)
- Re-validated temporal + embedding models with real classifier (Phase 1 blocker removed)

**Phase 2-4 (COMPLETE):** Cognitive Fable + Specifications + Robustness
- Implemented formal reframing policy (heuristic + learned variants)
- Wrote formal specifications (CFI, Fable)
- Added robustness layer (error handling, file limits, weight calibration)

**Phase 5 (CURRENT):** Research Pivot to Neuro-Symbolic
- Reframed entire project as doctoral research (OCD case study)
- Designed 4-layer architecture (LLM + NN + KG + Rules)
- **Next:** Clinical validation + Obsidian integration as research instrument

**Key Blocker Removed:** Classifier is now trained; temporal/embedding models validated.
Ready for real-world testing.

## Architecture: Four-Layer Neuro-Symbolic Design

### LAYER 1: Neural LLM (Flexible Reasoning)
**Purpose:** Understand unstructured clinical narratives  
**Implementation:**
- `src/models/reframing_dialogue.py::PromptBackend` — configurable LLM (local Ollama or
  cloud API) with system prompts tuned for CBT reasoning
- Input: patient narrative (unstructured text)
- Output: candidate distortion + confidence score
- **Why first:** Only neural models handle semantic richness of patient language

### LAYER 1.5: Predictive Neural Networks (Confidence & Prediction) ⭐ RESEARCH CONTRIBUTION
**Purpose:** Score Layer 1 output + predict temporal dynamics  
**Implementation:**
- `src/models/temporal_cfi.py` — Causal Transformer predicting next-turn distortion
  escalation. Answers: "Is patient escalating toward crisis?"
- `src/models/rigidity_embedding.py` — MiniLM fine-tuned contrastively on
  (rigid, flexible) pairs. Scores cognitive rigidity ∈ [0, 1].
- `src/metrics/cognitive_flexibility_index.py` — Computes CFI from distortion vector
  (single source of truth for all downstream logic)
- Ensemble: Weighted combination → final confidence score
- **Why this layer:** Neural networks excel at prediction; provides confidence signal
  to Layer 3 for extra scrutiny when uncertain

### LAYER 2: Knowledge Graph (Structured Domain)
**Purpose:** Structure clinical knowledge; guide reasoning  
**Instantiation (OCD case study):**
- Graph nodes: OCD obsessions (contamination, harm, sexual, religious, symmetry),
  symptoms, distortion patterns, treatment protocols, contraindications
- Query interface: "Given contamination_fear + high_rigidity, what is first-line
  treatment?" → Returns: ERP protocol with specific first step
- Implementation: In-memory graph (Neo4j-compatible structure), queryable via Python
- **Future:** Automatic KG construction (research direction, not current scope)
- **Not hardcoded:** OCD graph is domain-specific; architecture generalizes to
  depression, panic, etc. by swapping subgraph

### LAYER 3: Symbolic Rules (Verification) ⭐ INTERPRETABILITY GUARANTEE
**Purpose:** Guarantee safety and guideline compliance  
**Implementation:**
- `src/models/archetypes.py` + `cognitive_fable.py` — Rule-based policies
- Rule types:
  - Clinical guideline rules (CBT protocol compliance)
  - Safety rules (suicide risk, contraindications)
  - Consistency rules (does this contradict yesterday?)
- **Output:** Verified recommendation + explicit reasoning chain
  ```json
  {
    "recommendation": "Start ERP with graduated exposure",
    "reasoning": ["LLM detected: contamination_fear (0.78)",
                  "NN predicted: escalation risk", 
                  "KG queried: OCD→contamination→ERP",
                  "Rules verified: safety ✓, guidelines ✓"],
    "safety_flags": []
  }
  ```

### LAYER 4: Real-World Integration (Obsidian Plugin) ⭐ RESEARCH INSTRUMENT
**Purpose:** Deliver recommendations + collect feedback in clinical workflow  
**Implementation:**
- `obsidian-plugin/` — TypeScript plugin for Obsidian Vault
- User flow: patient writes in Obsidian → system processes (Layers 1-3) → 
  recommendation displayed → patient responds → clinician reviews → feedback logged
- **Critical:** Obsidian is not just UI. It's the data collection instrument for
  validating Q5 (real-world performance)
- Local-first: all data stored locally until clinician review
- Feedback loop: patient outcome + clinician rating → system learns (confidence
  calibration, future DPO training)

### Supporting Infrastructure
- `src/data_pipeline/` — Download ANGST/MHC/counseling datasets, weak-label, expand
  dialogues (SMILE), split train/val/test
- `src/db/` + `alembic/` — PostgreSQL + SQLAlchemy for multi-user sessions, JWT auth
- `src/metrics/composite_rigidity.py` — Blend 3 rigidity signals (classifier CFI,
  temporal prediction, embedding score) with learnable weights
- `src/evaluation/llm_judge.py` — LLM-as-evaluator for dialogue quality
- `src/api/main.py` — FastAPI endpoints: `/analyze`, `/reframe`, `/trajectory`,
  `/rigidity_score`, `/composite_rigidity`, `/feedback`
- `configs/*.yaml` — Taxonomy, CFI weights, model names, dialogue backend switch
- **Docs:**
  - `docs/RESEARCH_PROPOSAL.md` ⭐ — Full doctoral proposal (research questions, methodology, timeline)
  - `docs/ARCHITECTURE.md` — Component architecture and data flow overview
  - `docs/CFI_SPECIFICATION.md` — Formal definition of cognitive flexibility metric
  - `docs/FABLE_SPECIFICATION.md` — Formal spec of policy formalization
  - `docs/TAXONOMY.md` — CBT distortion definitions (5-type)
  - `docs/VALIDATION.md` — Honest training results (classifier F1, temporal AUROC, etc.)
  - `docs/DATA_QUALITY.md` — Weak-label quality report (inter-annotator agreement)
  - `docs/NICHE_ANALYSIS.md` — Why OCD as case study (vs panic, depression)
  - `docs/LICENSING.md` — Verified license registry for all dependencies

## Research Questions (From docs/RESEARCH_PROPOSAL.md)

**Primary Questions (Publishable):**
1. **Q1:** Can neuro-symbolic architecture produce more interpretable recommendations than LLM alone?
2. **Q2:** Does KG + rules reduce inconsistencies and ensure guideline adherence?
3. **Q3:** Do neural networks (NN layer 1.5) improve confidence calibration and escalation detection?
4. **Q4:** What graph representation best facilitates clinical reasoning?
5. **Q5 (Real-world):** Does architecture maintain accuracy in actual clinical workflow (Obsidian pilot)?

**Secondary Questions:**
6. **Q6:** When and why does the architecture fail? (Failure mode analysis)
7. **Tradeoff Q:** Interpretability vs. flexibility — where is optimal balance?

Each question has **specific metrics, baselines, and success criteria** (see RESEARCH_PROPOSAL.md § 5).

---

## Critical Constraints & Disclosures

### Data & Labeling
- All distortion labels are **LLM weak-labeled** (no clinician ground truth at scale).
  Always disclose as limitation in any publication; never claim clinical validity.
- Dataset is OCD-focused synthetic + public mental health text. Not clinician-curated.
- Weak-labeling was inter-annotator validated via automatic coherence check (88% agreement
  with clinical heuristics); full clinician spot-check is pending (separate validation task).

### Licensing
- `mental/mental-roberta-base` is **CC-BY-NC-4.0, gated** — non-commercial only.
  Never suggest commercial deployment without re-licensing. Requires HF_TOKEN + accepted
  terms at HuggingFace Hub.

### Clinical Scope
- **This is a research prototype, NOT a medical device.** Outputs must never be framed
  as diagnosis or treatment in public communications.
- Architecture is validated on OCD (case study). Generalization to other disorders is
  documented as future work; do not claim universal applicability.
- System is designed for **clinician support**, not standalone patient use. All real-world
  deployments require licensed mental health professional oversight.

### Architectural Decisions
- LLM backend is pluggable (local Ollama or cloud API via `configs/dialogue.yaml`).
  Always verify which provider is active before running.
- LoRABackend is intentionally unimplemented (no GPU confirmed). Do not attempt to activate.
- Knowledge Graph is currently hand-curated (OCD domain). Automatic KG construction is
  listed as future research (Phase 6+).

## Roadmap (4-Year Doctoral Arc)

**Year 1: Foundation (Q1-Q4 computation + bench validation)**
- Implement Layers 1-3 (LLM, NN, KG, Rules)
- Test Q1-Q4 using synthetic OCD cases
- Paper 1: "Neuro-Symbolic Reasoning for Clinical Decision Support" (ACM/NeurIPS tier)

**Year 2: Clinical Validation (Q5 real-world + Obsidian integration)**
- Deploy Layer 4 (Obsidian plugin)
- Pilot with 8-10 real OCD patients (6-8 weeks)
- Papers 2-3: Clinical validation + neural prediction results

**Year 3-4: Generalization & Defense**
- Extend to depression, panic (proof of generalizability)
- Finalize papers + thesis (full defense)
- Release software (GitHub + Obsidian plugin marketplace)

See `docs/RESEARCH_PROPOSAL.md` for full timeline and expected outputs.

---

## Reference Materials

### Research Proposal
- **`docs/RESEARCH_PROPOSAL.md`** — Master document (14k words). Contains:
  - Full motivation, state-of-art, architecture specs
  - 6 research questions with specific metrics
  - Methodology, evaluation framework
  - Expected publications, software, timeline
  - This is the "north star" for all development decisions

### Methodology Citations
- SMILE (multi-turn dialogue expansion technique)
- Chinese-MentalBERT (domain-adaptive pretraining template)
- CBT-LLM (5-type distortion taxonomy baseline)
- I-HOPE / DepMamba / multimodal repos (literature review only)
- Full licensing verified in `docs/LICENSING.md`

### Domain Knowledge
- `docs/TAXONOMY.md` — Formal definitions of 5 CBT distortions
- `docs/CFI_SPECIFICATION.md` — Mathematical definition of Cognitive Flexibility Index
- `docs/FABLE_SPECIFICATION.md` — Formal spec of reframing policy
- `docs/NICHE_ANALYSIS.md` — Why OCD (vs panic, depression) as case study

## Conventions

### Development
- Python 3.10+, `pyproject.toml` (`pip install -e ".[dev]"`).
- Tests: `pytest` — pure-logic tests (CFI, preprocessing) must run without GPU, network,
  or API keys. Encoder/API tests skipped via markers when unavailable.
- All tests passing is gate to any commit (71 tests, ruff lint clean).

### LLM Provider Strategy
- **LLM calls** go through `src/utils/llm_client.py` (provider-agnostic).
  Do not instantiate SDK/HTTP clients elsewhere.
- **Provider routing:** Set PER TASK in configs:
  - `llm.provider` (global default)
  - `configs/dialogue.yaml::prompt_backend.provider` (reframing LLM)
  - `configs/data.yaml::dialogue_expansion.provider` (synthetic dialogue generation)
  - `configs/data.yaml::judge.provider` (evaluation LLM)
- **Current posture:** ALL tasks local-first (`ollama`/qwen3:8b, free, no API key,
  no data leaves machine).
- **Upgrade path:** Switch generation/evaluation to `anthropic`/claude-fable-5 when
  budget/compliance allows. Flag that patient text then leaves machine (document
  in privacy disclosures).
- **Global override:** `NAUSICA_LLM_PROVIDER=anthropic` env var (for scripts, testing).

### Configuration & Code
- **Config over code:** Taxonomy labels, CFI weights, model names, distortion→technique
  mapping live in `configs/`, not hardcoded.
- **API keys:** Only via `.env` (see `.env.example`); never committed, never logged.
  Use `python-dotenv` via `src/utils/config.py`.
- **Domain knowledge:** CBT protocols, OCD treatment guidelines live in YAML/JSON configs,
  not Python code. This allows clinicians to tune behavior without retraining.

### Validation & Documentation
- **Honest reporting:** All papers/theses must disclose:
  - Weak-label limitations (no clinician ground truth)
  - Synthetic data for training (not real patient journeys)
  - Case study focus (OCD only; generalization untested)
  - Real-world validation status (pending Obsidian pilot)
- **Single source of truth:** CFI computation via `cognitive_flexibility_index.py::compute_cfi()`.
  All models (temporal, embedding, composite) derive from this. Never compute CFI elsewhere.
- **Documentation:** Update `docs/` alongside code. Specs in RESEARCH_PROPOSAL.md are the
  authoritative source of research direction.
