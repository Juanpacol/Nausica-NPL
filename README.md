# Nausica

**A neuro-symbolic architecture for interpretable clinical decision support,
instantiated on OCD via real-time cognitive distortion detection and evidence-based
CBT recommendation.**

Most mental-health NLP repos stop at an opaque classifier. Nausica instead integrates
four layers into a single pipeline — LLM flexibility, neural prediction, knowledge-graph
reasoning, and symbolic rule verification — so that every recommendation carries an
explicit, verifiable, clinically defensible reasoning chain:

1. **LLM (Layer 1)** — reads unstructured patient narrative, proposes a candidate
   cognitive distortion + confidence.
2. **Neural networks (Layer 1.5)** — score that confidence and predict temporal
   dynamics: a Causal Transformer forecasts next-turn distortion escalation, and a
   contrastively fine-tuned embedding model scores cognitive rigidity into the
   **Cognitive Flexibility Index (CFI)**, a continuous scalar in [0, 1].
3. **Knowledge graph (Layer 2)** — structures OCD-specific domain knowledge
   (obsessions, symptoms, distortion patterns, treatment protocols) and answers
   queries like "given contamination_fear + high_rigidity, what is first-line
   treatment?"
4. **Symbolic rules (Layer 3)** — verifies safety, clinical-guideline compliance, and
   cross-session consistency before anything reaches a clinician or patient.

A fifth layer, the **Obsidian plugin (Layer 4)**, delivers recommendations inside a
real clinical workflow and doubles as the research instrument for validating
real-world performance.

> Research prototype (doctoral project). **Not a medical device.** Outputs are never
> framed as diagnosis or treatment. Distortion labels are LLM weak-labeled — disclosed
> as a limitation, never claimed as clinical ground truth. Architecture is validated on
> OCD as a case study; generalization to other disorders is future work.

See **[docs/RESEARCH_PROPOSAL.md](docs/RESEARCH_PROPOSAL.md)** for the full doctoral
proposal (motivation, 6 research questions, methodology, 4-year roadmap, expected
publications) and **[CLAUDE.md](CLAUDE.md)** for a compact reference of the current
architecture, status, and development conventions.

## Setup

```bash
python3.11 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"            # core + tests
pip install -e ".[clustering]"     # optional: BERTopic mindset profiler
cp .env.example .env

# LLM provider — default is 100% local and free (no mental-health text leaves
# your machine): install Ollama, pull the model, start the server:
brew install ollama && ollama pull qwen3:8b && ollama serve
# (optional alternative: set NAUSICA_LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY)
```

`HF_TOKEN` is needed for the gated `mental/mental-roberta-base` encoder
(CC-BY-NC-4.0 — see [docs/LICENSING.md](docs/LICENSING.md)); without it the code
falls back to `roberta-base`.

## Pipeline (in order)

```bash
# 1. Download source datasets (ANGST, Mental Health Classification, Amod counseling)
python -m src.data_pipeline.download_datasets

# 2. Consolidate + clean into one corpus
python -m src.data_pipeline.preprocessing consolidate

# 3. Weak-label with the CBT distortion taxonomy (start with --limit 100 to gauge cost)
python -m src.data_pipeline.weak_labeling \
  --input data/processed/texts.jsonl --output data/processed/weak_labeled.jsonl --limit 100

# 4. Split train/val/test
python -m src.data_pipeline.preprocessing split

# 5. Fine-tune the distortion classifier
python -m src.models.distortion_classifier train

# 6. Generate synthetic multi-turn reframing dialogues (SMILE-style, English)
python -m src.data_pipeline.dialogue_expansion --limit 50

# 7. Evaluate dialogues with LLM-as-judge
python -m src.evaluation.llm_judge \
  --input data/synthetic/dialogues.jsonl --output results/judge_scores.jsonl

# 8. Set up the database (Postgres; Homebrew or docker compose up -d db)
pip install -e ".[db]"
createdb nausica            # or: docker compose up -d db  (+ DATABASE_URL in .env)
alembic upgrade head

# 9. Serve the API
uvicorn src.api.main:app --reload
```

Or run the pipeline end-to-end via `scripts/run_data_pipeline.sh`.

## API

All data endpoints require a Bearer JWT (`POST /auth/register` → token).

| Endpoint | What it does |
|---|---|
| `POST /auth/register` · `/auth/login` | email + password → JWT |
| `POST /analyze` | text → per-distortion probabilities + CFI (persisted) |
| `POST /analyze/audio` | voice note → local Whisper transcript → same pipeline |
| `POST /reframe` | text (+ optional `session_id`) → Socratic reply + CFI delta; RAG-augmented with the user's own past effective reframes |
| `GET /trajectory/{session_id}` | CFI evolution across the session's turns |
| `POST /predict_trajectory` | distortion history → predicted next-turn vector |
| `POST /rigidity_score` | text → embedding-axis rigidity score |
| `POST /composite_rigidity` | text → blend of all three rigidity signals |
| `GET /profile/archetype` | dominant mindset archetype + trend over the user's history |
| `GET\|POST /profile/consent` | read / grant / revoke clinician visibility (opt-in) |
| `GET /org/patients` | clinician dashboard: consenting patients + archetype + latest CFI |
| `GET /reports/{user_id}.pdf` | clinical progress report (self, or clinician with consent) |
| `POST /turns/{id}/feedback` | clinician marks reframe quality (future DPO data) |

## Tests

```bash
pytest            # pure-logic tests run anywhere; model tests skip without encoder access
```

## Documentation

- [CLAUDE.md](CLAUDE.md) — compact project context (architecture, status, constraints, conventions)
- [docs/RESEARCH_PROPOSAL.md](docs/RESEARCH_PROPOSAL.md) — full doctoral proposal: research questions, methodology, timeline
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — component architecture and data flow overview
- [docs/CFI_SPECIFICATION.md](docs/CFI_SPECIFICATION.md) — formal definition of the Cognitive Flexibility Index
- [docs/FABLE_SPECIFICATION.md](docs/FABLE_SPECIFICATION.md) — formal spec of the reframing policy
- [docs/TAXONOMY.md](docs/TAXONOMY.md) — distortion definitions + CFI weight rationale
- [docs/LICENSING.md](docs/LICENSING.md) — verified license register for every external asset
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md) — weak-label spot-check results
- [docs/VALIDATION.md](docs/VALIDATION.md) — training results (classifier F1, temporal AUROC, etc.)
- [docs/NICHE_ANALYSIS.md](docs/NICHE_ANALYSIS.md) — why OCD as case study (vs panic, depression)
