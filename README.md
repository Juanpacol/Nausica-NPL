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
cp .env.example .env               # then fill in ANTHROPIC_API_KEY (+ HF_TOKEN)
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

# 8. Serve the API
uvicorn src.api.main:app --reload
```

## API

| Endpoint | What it does |
|---|---|
| `POST /analyze` | text → per-distortion probabilities + CFI |
| `POST /reframe` | text (+ optional `session_id`) → Socratic counselor reply + CFI delta |
| `GET /trajectory/{session_id}` | CFI evolution across the session's turns |

## Tests

```bash
pytest            # pure-logic tests run anywhere; model tests skip without encoder access
```

## Documentation

- [CLAUDE.md](CLAUDE.md) — compact project context (architecture, constraints, conventions)
- [docs/TAXONOMY.md](docs/TAXONOMY.md) — distortion definitions + CFI weight rationale
- [docs/LICENSING.md](docs/LICENSING.md) — verified license register for every external asset
- [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md) — weak-label spot-check results (filled during Phase 1)
