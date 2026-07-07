# Nausica

**Cognitive distortion detection + CBT Socratic reframing, measured by a continuous
Cognitive Flexibility Index (CFI).**

Most mental-health NLP repos stop at binary classification ("depressed / not depressed").
Nausica instead:

1. **Detects 5 cognitive distortion types** (multi-label, CBT taxonomy: all-or-nothing,
   overgeneralization, emotional reasoning, catastrophizing, mind reading).
2. **Aggregates them into the CFI** — a continuous cognitive-rigidity scalar in [0, 1],
   not a diagnostic label.
3. **Runs a Socratic reframing dialogue** (CBT downward-arrow technique) and evaluates
   success as *CFI trending downward across turns* — a "reframing trajectory".

> ⚠️ Research prototype for a graduate scholarship project. **Not a medical device.**
> Outputs are never diagnoses. Labels are LLM weak-labeled (disclosed limitation).

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

# 3. Weak-label with the 5-type taxonomy (start with --limit 100 to gauge cost)
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

- [CLAUDE.md](CLAUDE.md) — compact project context (architecture, constraints, conventions)
- [docs/TAXONOMY.md](docs/TAXONOMY.md) — distortion definitions + CFI weight rationale
- [docs/LICENSING.md](docs/LICENSING.md) — verified license register for every external asset
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md) — weak-label spot-check results (filled during Phase 1)
