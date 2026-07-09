# Cognitive Fable — Formal Specification

Formalization of the reframing policy layer. Implementation:
`src/models/cognitive_fable.py`; integration:
`src/models/reframing_dialogue.py` (PromptBackend); tests:
`tests/test_cognitive_fable.py`.

Naming note: "Cognitive Fable" is this project's formal policy model — distinct
from Claude Fable, the Anthropic LLM used as generation backend
(configs/dialogue.yaml).

## Motivation

Prompt-only reframing systems (CBT-LLM and, previously, this project's
PromptBackend) leave the *therapeutic strategy* implicit inside a free-form LLM
generation: which technique was used, and why, is unknowable after the fact.
The Cognitive Fable factors that decision out of the LLM:

```
observe                      decide                      execute
DistortionClassifier  ──►  FableState ──policy──► FableAction ──►  LLM constrained
(+ session position)       (auditable)            (logged)         by the action
```

The LLM still writes the words; the *strategy* is chosen by an inspectable
policy **before** the call, logged, and auditable.

## Formal model

**State** (`FableState`): everything the policy sees.

```
S = (d, t)      d ∈ [0,1]^5   distortion probability vector (taxonomy order)
                t ∈ ℕ         1-based client-turn index within the session
```

**Action** (`FableAction`): the chosen strategy.

```
A = (technique, target, tone)
technique ∈ {downward_arrow, evidence_exam, behavioral_exp, spectrum, socratic}
target    ∈ L ∪ {none}          strongest detected distortion
tone      ∈ {validating, gently_challenging, exploratory}
```

**Policy**: π : S → A. Two interchangeable implementations, selected in
configs/model.yaml (`cognitive_fable.policy`):

### π_heuristic (`default_policy`) — deterministic, config-driven

```
target    = argmax_i d_i                     (ties: taxonomy order; all-zero → none)
technique = technique_map[target]            (fallback_technique if unmapped)
tone      = first severity band with d_target ≥ min_prob
```

The technique map encodes CBT-canonical pairings (catastrophizing →
downward-arrow, overgeneralization → evidence examination, mind-reading →
behavioral experiment, all-or-nothing → spectrum thinking); the severity bands
encode "validate first when the client is deeply stuck". Both live in
configs/model.yaml so clinicians tune them **without retraining anything** —
the same design as `archetypes.py`.

### π_learned (`FablePolicyNet`) — small two-head MLP

```
input   x = [d ; min(t, 16)/16]              ∈ ℝ^6
trunk   h = ReLU(W₁x)                        hidden_dim = 32
heads   technique ~ softmax(W_tech h)        tone ~ softmax(W_tone h)
```

Trained on (state, technique, tone) tuples extracted from the synthetic
dialogues by an LLM annotator
(`src/data_pipeline/build_fable_policy_dataset.py`) — the same
weak-supervision pattern as `temporal_cfi.py` and `rigidity_embedding.py`,
with the same disclosed caveat: it validates the policy architecture, **not
clinical optimality**. Missing checkpoint ⇒ graceful fallback to π_heuristic.
Training reports held-out accuracy for BOTH policies against the LLM
annotations, win or lose (docs/VALIDATION.md).

## Execution

When `configs/dialogue.yaml: prompt_backend.use_fable` is true, PromptBackend
computes the action and appends an explicit strategy block to the Socratic
system prompt (technique + tone, each with one guidance sentence —
`FABLE_CONSTRAINT_TEMPLATE`). `use_fable: false` reproduces the exact
pre-Fable free-form behavior.

Safety is **not** the Fable's job: crisis handling stays in the base
`SOCRATIC_SYSTEM_PROMPT` (unconditional instruction to drop technique on any
self-harm signal). The classifier has no crisis label, and inventing one here
would be an unvalidated clinical claim.

## Comparison vs prompt-only reframing

| Property | Prompt-only (CBT-LLM style) | **Cognitive Fable** |
|---|---|---|
| Strategy decided by | LLM, implicitly, per token | explicit policy, before the call |
| Auditability | transcript archaeology | action logged per turn |
| Testability | needs an LLM + judge | π_heuristic is pure logic (9 unit tests, no LLM) |
| Clinician control | edit prose prompt, hope | edit technique_map / severity_bands in YAML |
| Ablatable | no | yes — same LLM with/without constraint, judge scores compare |
| Improvable from feedback | full fine-tune | retrain the 6-input policy net (or later: DPO) |

## Evaluation plan

1. **Policy agreement** — π_learned vs π_heuristic held-out accuracy against
   LLM annotations (reported by `python -m src.models.cognitive_fable train`).
2. **Ablation** — judge scores (`src/evaluation/llm_judge.py` rubric) for
   dialogues generated with `use_fable: true` vs `false`, same LLM, same
   client openings.
3. **Outcome-linked** (needs real data) — do Fable-constrained sessions show
   larger CFI decreases? Uses the same trajectory machinery as the headline
   evaluation.

## Known limitations

1. Both the dialogues and the technique annotations behind π_learned are
   synthetic/LLM-derived (no clinician-labeled technique ground truth yet).
2. The state is memoryless beyond the turn index — no representation of what
   was already tried in the session (future work: condition on action history).
3. Technique vocabulary is 5 coarse classes; real CBT practice is finer.

## Results

> _pending — fill after `build_fable_policy_dataset.py` + training run
> (blocked on the Phase 1 classifier fine-tune; see docs/VALIDATION.md)._
