# Nausica — Implementation Plan (Post-Audit, Definitive)

**Status:** Authoritative plan incorporating all F2 audit findings. Supersedes phase ordering
in prior roadmap docs.
**Audience:** Direct input for code-skeleton generation (Phases 8-10) and the single source
of truth for Phases 6-11.
**Timeline:** Solo researcher, 12-16 weeks (Phases 6-11). Phases 1-5 complete.
Phase 12+ (clinical validation) is a separate future project.

---

## 1. Executive Summary

**Neuro-Symbolic Clinical Reasoning on OCD:** a 4-layer architecture integrating a generative
LLM (Layer 1), neural confidence and escalation prediction (Layer 1.5), structured
knowledge-graph reasoning (Layer 2), and symbolic rule verification (Layer 3), delivered
through a clinician-gated Obsidian workflow (Layer 4).

**Year 1 claim (this plan):** the architecture is validated **in vitro** — bench validation
of Q1-Q3, a technical ablation for Q4, and a usability smoke-test for Q5 — across Phases 6-11
in 12-16 weeks. **Real-world efficacy (Phase 12+) is future work requiring IRB approval and
real patients**; nothing in Year 1 claims clinical efficacy.

**Distinctive strength:** a *pre-generation* policy (Fable) decides technique and tone
**before** the LLM generates, making the output *inherently* interpretable — as opposed to
post-hoc explanation of an already-opaque generation. Combined with neural confidence gating
and an auditable reasoning chain at every layer, this is the delta over prior art (§2).

---

## 2. Research Focus (Rectified)

### The gap (corrected per F2)

The original claim ("no published work combines LLMs with symbolic verification in clinical
decision support") is **false** and is retired. The corrected framing:

- **Neural (LLM):** flexible, handles unstructured narrative — but opaque and inconsistent.
- **Symbolic (KG/rules):** interpretable and verifiable — but brittle and hand-curated.
- **State of the art:** OR-chains (LLM → KG filter, strictly sequential) or hybrid
  LLM + guardrails (NeMo Guardrails, DSPy assertions) — none carries a neural confidence
  signal into the symbolic layer.
- **Related work that must be cited:**
  - **Arden Syntax** — 30 years of computable clinical guidelines (symbolic only, no
    free-text understanding).
  - **GLIF / PROforma** — formal clinical decision protocols (guideline formalisms, no
    generative or neural layer).
  - **MindMap** (Wen et al. 2024) — KG-prompting of medical LLMs; the LLM remains the final
    arbiter, no independent symbolic verification.
  - **DR.KNOWS** — diagnosis-guided KG + LLM; KG informs generation but does not gate it.
  - **GraphCare** — personalized KG construction for clinical prediction; predictive, not
    generative, no rule-based safety verification.
- **Nausica's delta:** (a) integration *before* generation — the Fable policy selects
  technique/tone pre-generation; (b) **neural confidence** (temporal CFI + rigidity) as an
  explicit gating signal to the symbolic layer; (c) **formal measurement of
  interpretability** (IFS metric); (d) a **real workflow** (Obsidian +
  clinician-in-the-loop) as research instrument.

### Why OCD

- **Clear diagnostic criteria** (DSM-5) — a well-bounded domain to encode.
- **Standardized ERP protocols** — something concrete to verify against (Layer 3 needs
  ground rules to exist).
- **Rich clinical narratives** — a genuine test for the neural layer.
- **Unmet need:** 8-17 years average to diagnosis; acute shortage of ERP therapists
  (especially in LATAM).
- **Transferable:** same stack, different KG/ruleset → depression, panic (future work).

### Scope / No-scope

- ✓ Bench validation: Q1-Q3 in vitro; Q4 technical ablation; Q5 usability smoke-test.
- ✗ Clinical efficacy (Q1-human, Q4-human, Q5-efficacy): **Phase 12+ with IRB**, not Year 1.
- ✗ Automatic KG construction: future research.
- ✗ GPU/LoRA fine-tuning: no hardware confirmed; deferred.
- ✗ Commercial deployment: blocked by CC-BY-NC checkpoint license.

---

## 3. Architecture (Corrected Technical Specification)

### Layer 1 — Neural LLM (Flexible Reasoning)
- **Input:** unstructured patient text. **Output:** candidate distortion + confidence ∈ [0,1].
- **Implementation:** `src/models/reframing_dialogue.py::PromptBackend` via
  `src/utils/llm_client.py`, Ollama/qwen3:8b (local).
- **Why first:** only neural models handle the semantic richness of patient language.

### Layer 1.5 — Predictive Neural Networks (Confidence & Escalation) — *ensemble corrected*
- **Temporal CFI Transformer** (`src/models/temporal_cfi.py`): predicts next-turn distortion
  vector; escalation = ||distortion_t+1|| > threshold.
- **Rigidity Embedding** (`src/models/rigidity_embedding.py`): MiniLM fine-tuned
  contrastively on (rigid, flexible) pairs; outputs rigidity ∈ [0,1].
- **Ensemble (F2 correction):** `confidence = weighted_mean([LLM_confidence,
  temporal_confidence])` — a combination of *epistemic* signals only. **Rigidity MODULATES
  the recommendation** (e.g., high rigidity → suggest a less demanding exposure first);
  it is **never averaged into confidence**. They are different quantities.
- Low confidence triggers extra scrutiny in Layer 3 (stricter thresholds, mandatory
  clinician-review flag). CFI single source of truth remains
  `src/metrics/cognitive_flexibility_index.py::compute_cfi()`.

### Layer 2 — Knowledge Graph (Structured Domain) — *invariant added*
- **Content:** ~40 nodes (obsessions: contamination, harm, sexual, religious, symmetry;
  symptoms; distortion patterns; ERP steps; contraindications) and ~50 edges
  (symptom→obsession, obsession→distortion, distortion→CBT_technique, technique→ERP_protocol,
  protocol→contraindication, patient_state→escalation_risk).
- **Invariant (F2):** Layer 2 = **declarative facts/structure only**. No inference logic
  lives in the graph.
- **Implementation:** `networkx` (lightweight, in-memory, debuggable), queryable via Python.
  Query: `query_treatment(obsession, distortion, rigidity)` → ERP protocol recommendation.
- **Content source:** `configs/knowledge_graph/ocd_nodes.yaml`, `ocd_edges.yaml` —
  hand-curated with clinical expert veto (Phase 6).

### Layer 3 — Symbolic Rules (Verification & Gating) — *invariant added*
- **Input:** candidate recommendation (Layers 1-2), patient history, session state.
- **Rules:** ~50 (safety: suicide risk, contraindications; clinical: ERP protocol
  compliance; consistency: contradiction with history).
- **Invariant (F2):** Layer 3 = **procedural inference over Layer 2 facts + Layer 1.5
  confidence + patient state**. All conditional logic lives here, never in the KG. KG
  answers "what is true in the domain"; Rules answer "what follows for this patient".
  If a rule gates a recommendation, the reasoning is explicit.
- **Implementation:** custom YAML-driven engine (not Rete/experta) —
  `src/rules_engine/engine.py` (RuleSet, Condition, Action, `apply_rules()`),
  `src/rules_engine/verification.py` (`verify_recommendation()` → VerifiedRecommendation:
  recommendation + reasoning_chain + flags), `configs/rules.yaml`.
- **Output:** reasoning_chain JSON — every step records which layer, what signal, why it
  passed or failed. Makes compliance auditable; catches failures before any user sees them.

### Layer 4 — Real-World Integration (Obsidian Plugin) — *safety conflict resolved*
- **Patient surface:** patient writes in the Obsidian vault; system processes Layers 1-3.
- **Clinician gate (F2 resolution):** the recommendation is **held until a clinician
  approves it (or provides an alternative) before the patient sees anything**. Patient sees
  the approved recommendation + full reasoning chain, **or** generic psychoeducation if not
  approved. "Clinician support only" is structurally enforced, not aspirational.
- **Feedback loop:** clinician rates quality (future DPO training); patient outcome logged.
  Critical for Q5 and for confidence calibration.

### Stack decisions (ratified)

| Component | Decision | Rationale |
|---|---|---|
| LLM | Ollama/qwen3:8b (local) | Free, reproducible, no patient data leaves machine |
| KG | `networkx` (not Neo4j) | ~40 nodes need no DB; no ops overhead for research |
| Rules | Custom YAML engine (not Rete) | Simple, debuggable; aligns with existing `archetypes.py` + `cognitive_fable.py` patterns; clinicians edit YAML, not code |
| DB / API | PostgreSQL + SQLAlchemy / FastAPI | Existing, robust |
| Plugin | TypeScript (Obsidian standard) | Existing shell |
| Tests | pytest, 100% pass gate | Existing convention |

---

## 4. Implementation Phases (12-16 weeks, solo)

### Phases 1-5 — COMPLETE (summary)
- **Phase 1:** 3000 texts weak-labeled; DistortionClassifier trained; temporal/embedding
  models validated with the real classifier.
- **Phases 2-4:** `cognitive_fable.py`, `archetypes.py`, formal specs (CFI, Fable),
  robustness layer.
- **Phase 5:** 4-layer architecture designed; RESEARCH_PROPOSAL.md; research questions
  formulated.

### Phase 6 — Clinical KG Curation *(NEW, weeks 1-3, critical path)*
- **Objective:** specify the ~40 nodes + ~50 edges of the OCD graph.
- **Process:** collaborate with an OCD/ERP clinical expert (psychologist) **with veto over
  content**, defining node types (obsessions, symptoms, distortion patterns, ERP exposures,
  first- vs second-line protocols), edge types (symptom→obsession, obsession→distortion,
  distortion→CBT_technique, technique→ERP_step, ERP_step→contraindication), and metadata
  (DSM-5 codes, prevalence, severity scale). The same expert curates the Q2 checklist —
  independent of the rules engine, which breaks the Q2 circularity.
- **Output:** `configs/knowledge_graph/ocd_nodes.yaml`, `ocd_edges.yaml` (content only, no
  code). **Blocks:** Phases 8-9 content, Phase 11 Q2.
- **Success:** expert sign-off on nodes/edges/contraindications.

### Phase 7 — Dialogue Corpus Scaling *(NEW, weeks 2-3, parallel to Phase 6)*
- **Objective:** 100+ synthetic multi-turn OCD dialogues (≥7 turns each) for temporal CFI
  training.
- **Process:** SMILE technique + expanded `src/data_pipeline/dialogue_expansion.py`.
- **Output:** `data/synthetic/dialogues_v2.jsonl`; train/val/test split; distortion
  trajectory computed per dialogue. **Blocks:** Phase 11 Q3.
- **Success:** 100+ dialogues, ≥7 turns each, split done, trajectories computed.

### Phase 8 — Layer 3 Core: Rules Engine (weeks 4-6)
- **Objective:** implement the symbolic rules layer completely.
- **Modules:** `src/rules_engine/__init__.py`; `src/rules_engine/engine.py` (RuleSet loads
  YAML; `apply_rules(text, state, rules)` → list of (rule_id, passed, reasoning));
  `src/rules_engine/verification.py` (`verify_recommendation(candidate_rec, context, rules)`
  → VerifiedRecommendation(recommendation, reasoning_chain: List[str], flags: List[str]));
  `configs/rules.yaml` (~50 rules: clinical-guideline, safety, consistency).
- **API:** `/recommend` skeleton (text + session_history → recommended technique,
  reasoning_chain, confidence, safety_flags); full wiring in Phase 9.
- **Tests:** 20+ unit tests (rules without KG; mocked KG queries). **Blocks:** Phase 9.
- **Success:** 20+ tests pass; all rules parseable from YAML; endpoint callable.

### Phase 9 — Layer 2 + Integration (weeks 6-9)
- **Objective:** implement the Knowledge Graph and integrate with Layer 3.
- **Modules:**
  - `src/knowledge_graph/schema.py` — NodeType, EdgeType, Node, Edge, OCD enums.
  - `src/knowledge_graph/ocd_graph.py` — `build_graph(nodes_yaml, edges_yaml)` →
    `networkx.DiGraph`; `query_treatment(obsession, distortion, rigidity)` →
    (ERP_protocol, steps, contraindications); `explain_path(start, end)` → edge chain
    (reasoning for why protocol matches obsession).
  - `src/models/reasoning_pipeline.py` — `orchestrate(patient_text, session_history)`:
    Layer 1 LLM → distortion; Layer 1.5 NN → confidence + rigidity; Layer 2 KG →
    protocol; Layer 3 rules → `verify_recommendation()`; returns VerifiedRecommendation JSON.
  - `configs/knowledge_graph.yaml` — references Phase 6 YAML content.
- **API:** `POST /recommend` (complete); `GET /kg/query?obsession=X&distortion=Y`;
  `GET /kg/explain_path?from=X&to=Y`.
- **Integration test:** 30 synthetic OCD cases (distortion detected → KG query → protocol
  found → rules verify → reasoning chain returned). **Blocks:** Phases 10 and 11.
- **Success:** 30/30 integration tests pass; all endpoints callable; reasoning chains
  valid JSON.

### Phase 10 — Layer 4: Obsidian Plugin Wiring (weeks 9-11)
- **Objective:** connect Layers 1-3 into Obsidian with the clinician approval gate.
- **Modules:** `obsidian-plugin/src/RecommendationModal.ts` (display recommendation +
  reasoning chain; clinician approve/reject/edit; patient sees approved output or generic
  psychoeducation); `obsidian-plugin/src/api.ts` additions (`getRecommendation()`,
  `submitApproval()`, `submitFeedback()`); Alembic migration adding `recommendations`
  table (id, user_id, session_id, recommendation_json, clinician_id, approved_at,
  feedback_rating).
- **Safety:** recommendation stored but **not shown to patient until
  `clinician.approved = true`**.
- **End-to-end flow:** patient writes → `/recommend` → held → clinician notified → modal →
  approve/edit → patient sees approved → patient rates → feedback logged.
- **Success:** end-to-end flow works locally; approval gate functional; feedback persists.

### Phase 11 — Bench Validation: Q1-Q5 In Vitro (weeks 11-16)
- **Objective:** validate the research questions without real patients (Phase 12+ handles
  real-world claims).
- **Q1 (Interpretability):** 30 OCD cases → full pipeline reasoning chains vs LLM-only
  baseline (with CoT prompt). LLM-judge compares fidelity — **disclosed as preliminary,
  not clinician-rated**. IFS metric as proxy. Report: IFS full vs IFS LLM-only, by how much.
- **Q2 (Consistency & Compliance):** 50 synthetic cases with known correct protocols.
  Consistency (same input → same output) > 95%? Guideline compliance (protocol matches the
  Phase 6 expert checklist) > 99%? Report: % passing.
- **Q3 (Calibration & Escalation):** scaled corpus (Phase 7), train/val/test. ECE < 0.10?
  Escalation AUROC > 0.75 (escalation = ||distortion_t+1|| > 2·std(distortion_t))?
  **Disclosed:** escalation labels are model-generated proxies, not real follow-up.
  Report: ECE, AUROC, per-bin calibration.
- **Q4 (KG Representation):** technical ablation only — query speed (networkx vs
  hypothetical Neo4j), edge expressivity, maintenance cost. Reframed as a technical
  question, not clinician-rated. Alternative: cut Q4 from Phase 11 entirely and defer to
  a Phase 12+ expert panel.
- **Q5 (Real-World Workflow):** deploy Obsidian locally; smoke-test with 2-3 clinicians
  (**not patients; no IRB yet**). Measure: modal renders, gate works, clinicians find it
  usable. **Disclosed:** usability test, not efficacy.
- **Output:** `docs/BENCH_VALIDATION_RESULTS.md` — honest report per question, including
  limitations. Results inform what is ready for the Phase 12+ pilot.

### Phase 12+ — Clinical Validation with Real OCD Patients *(FUTURE, NOT Year 1)*
- **Objective:** Q1-human (clinician ratings), Q4-human (expert panel), Q5-efficacy
  (patient outcomes).
- **Scope:** IRB protocol, recruitment, 8-10 OCD patients, 6-8 week pilot.
- Documented here only so no earlier phase claims what Phase 12+ must deliver.

### Timeline & critical path

```
Phase 6 (KG curation, w1-3) ────────┐
Phase 7 (corpus, w2-3, parallel) ───┼─► Phase 9 (w6-9) ─► Phase 10 (w9-11) ─► Phase 11 (w11-16)
Phase 8 (rules engine, w4-6) ───────┘
```
6/7/8 may overlap; 9 → 10 → 11 is strictly sequential. A 2-week buffer for unknowns is
embedded in the 12-16 week estimate.

---

## 5. Research Questions (Fully Specified)

| # | Question | Metric / Success criterion | Phase | Validated as | Future |
|---|---|---|---|---|---|
| Q1 | Does NSCR produce more interpretable recommendations than LLM-only? | IFS +25% over LLM-only (CoT baseline) | 11 | Auto-judge (preliminary, disclosed) | Phase 12+ clinician-rated |
| Q2 | Do KG+rules reduce inconsistency & ensure guideline compliance? | Consistency > 95%; compliance > 99% (independent expert checklist) | 11 | In vitro ✓ | N/A |
| Q3 | Do NN layers improve calibration & escalation detection? | ECE < 0.10; escalation AUROC > 0.75 (synthetic labels, disclosed) | 11 | In vitro ✓ (proxy labels) | Phase 12+ real escalation |
| Q4 | Which KG representation best serves clinical reasoning? | Technical ablation (speed, expressivity, maintenance) | 11 | Technical only (or cut) | Phase 12+ expert panel |
| Q5 | Does the architecture hold up in a real workflow? | Usability in Obsidian, 2-3 clinicians smoke-test | 11 | Local smoke-test ✓ | Phase 12+ patient efficacy |

---

## 6. Success Criteria (Per Phase)

| Phase | Done when |
|---|---|
| 6 | Expert-approved KG spec: nodes, edges, contraindications curated and signed off |
| 7 | 100+ dialogues ≥7 turns; train/val/test split; distortion trajectories computed |
| 8 | 20+ unit tests pass; `rules.yaml` valid; `/recommend` skeleton callable |
| 9 | 30/30 integration tests pass; all endpoints callable; reasoning chains valid JSON |
| 10 | Obsidian modal renders; approval gate functional; feedback persists |
| 11 | Honest bench report: Q1-Q3 results + caveats; Q4 technical assessment; Q5 usability feedback |

---

## 7. Critical Notes

**Security & regulatory**
- Clinician approval **before** the patient sees any recommendation (otherwise generic
  psychoeducation only). Enforced in the plugin, not by convention.
- Research prototype, **not a medical device**; all outputs marked accordingly.
- All patient text stays local (Obsidian + local PostgreSQL).
- Weak-label limitations disclosed in every publication.
- License: classifier checkpoint is CC-BY-NC-4.0 (gated) — non-commercial only.

**Known limitations (disclose always)**
- All labels are LLM weak-labeled; no clinician ground truth at scale.
- Q3 escalation labels are synthetic/proxy; real escalation needs Phase 12+ follow-up.
- Phase 11 is in vitro (bench); real-world validation is Phase 12+ (clinical).
- No GPU available; LoRA not implemented.

**Timeline assumptions**
- 12-16 weeks, solo researcher, Phases 6-11; Phases 1-5 complete.
- Phase 12+ is a separate clinical-trial project beyond Year 1.
- 2-week buffer for unknowns embedded in the estimate.

---

**This plan is executable. Sonnet will now produce code skeletons (signatures + docstrings
only) for Phases 8-10, ready for implementation.**
