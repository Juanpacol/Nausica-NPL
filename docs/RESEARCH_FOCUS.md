# Research Focus — Nausica

**Neuro-Symbolic Clinical Reasoning for Interpretable LLM-Based Decision Support, Validated on OCD**

*Executive summary of the doctoral research focus. Full detail: [`RESEARCH_PROPOSAL.md`](RESEARCH_PROPOSAL.md); domain-selection analysis: [`NICHE_ANALYSIS.md`](NICHE_ANALYSIS.md); architecture and metric specifications: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`CFI_SPECIFICATION.md`](CFI_SPECIFICATION.md), [`FABLE_SPECIFICATION.md`](FABLE_SPECIFICATION.md).*

---

## 1. The Problem

Large Language Models understand nuanced patient language better than
any prior technology, yet their deployment in clinical settings is
blocked by a critical barrier: **interpretability and verifiability**.
When an LLM recommends a therapeutic intervention, clinicians and
regulators need to know *why* it was recommended, *what evidence*
supports it, *whether it complies* with clinical guidelines, and
*how confident* the system is.

The gap statement below traces five generations of prior work — each
solving part of the problem — to establish precisely where Nausica's
contribution sits and why the combination, not any single piece, is
the research opportunity.

---

### Part A: Classical Symbolic Approaches (1988–2001)

**Symbolic diagnosis and rule-based systems** established that clinical
knowledge can be formalized and executed:

- **Symbolic Diagnosis Formalization** [1]: Lucas (1997) formalizes
  diagnostic reasoning into symbolic knowledge — foundational proof
  that clinical reasoning is codifiable.
- **Rule-Based Diagnostic Classification** [2, 3]: Huang et al. (2015)
  and Choubey et al. (2017) build interpretable rule-based diagnosis
  systems (diabetic nephropathy, diabetes). Explicit rules produce
  transparent, auditable decisions.
- **Arden Syntax (ASTM E1762, HL7 Standard, 1989–present)** [Seitinger
  et al. 2014]: Medical Logic Modules (MLMs) represent clinical
  guidelines as executable decision trees. Seitinger et al. merged
  three Lyme borreliosis guidelines into a single Arden Syntax
  knowledge base, demonstrating that (a) medical knowledge can be
  separated from technical implementation, (b) guidelines from
  multiple sources can be reconciled into one formal structure, and
  (c) fuzzy logic extensions handle clinical uncertainty (linguistic
  terms like "possibly present" mapped to [0,1] certainty). 25+ years
  in production clinical decision support systems.
- **GLIF (Guideline Interchange Format, 1996–present)** [Boxwala et
  al. 2004; Peleg et al. 2003]: Object-oriented, three-level
  representation (conceptual → computable → implementable) enabling
  sharable computer-interpretable guidelines across institutions.

**Limitation:** Cannot understand rich, unstructured patient
narratives. Requires manually structured input (lab values, checkbox
symptoms). Brittle on novel or nuanced cases.

---

### Part B: Multi-Layer Neural Approaches (2016–2024)

Researchers explored **layered/ensemble neural architectures** to
improve diagnostic accuracy — establishing that "layering signals
improves reasoning," a principle Nausica's Layer 1.5 builds on:

- **Multi-Layer Classifier Frameworks** [4]: Bashir et al. (2016)
  stack multiple classifiers for disease prediction (HMV framework).
- **Feature Selection & Optimization** [5, 6, 7]: PSO-optimized SVM
  for liver disease (Joloudari et al. 2019); heart disease prediction
  deployed in real clinical settings (Fitriyani et al. 2020; Rani et
  al. 2021).
- **Attention-Based Temporal Modeling** [8]: Ma et al. (2017), DIPOLE
  — bidirectional attention-based RNNs for diagnosis prediction,
  capturing *temporal dynamics* in patient history. Direct
  architectural precedent for Nausica's Layer 1.5 temporal CFI
  transformer (predicting escalation from sequential patient data).
- **Deep Learning for Complex Diagnosis** [9, 10]: Cancer diagnosis
  (Tufail et al. 2021) and COVID-19 detection (Liu et al. 2022) via
  deep learning on complex/high-dimensional medical data.
- **Temporal Escalation Prediction — Psychiatric Precedent**: Unlike
  DIPOLE's general disease-trajectory modeling, three studies establish
  that *escalation* specifically is predictable in real psychiatric
  populations. Su et al. (2020, *Translational Psychiatry*) predict
  suicide risk in children/adolescents from EHR data across **multiple
  prediction windows (0–365 days)** using sequential forward feature
  selection, AUC 0.81–0.86, and show that predictor importance shifts
  between short- and long-term windows. Meyer et al. (2022,
  *Psychological Medicine*) go further methodologically: using a
  smartphone daily-sampling app (Sleepsight) and a **Differential
  Time-Varying Effect Model (DTVEM)**, they identify specific **lag
  windows (1–8 and 1–12 days)** at which sleep disturbance predicts
  psychosis symptom deterioration, with negative affect as a
  significant mediator — a digital, fine-grained, lag-structured
  approach directly analogous to what Nausica's Layer 1.5 temporal CFI
  transformer must do with patient narrative sequences. Chen et al.
  (2026, *Lancet Psychiatry*) use latent trajectory (finite mixture)
  models on adolescent life-event exposure to classify risk
  trajectories predictive of suicidal ideation, showing trajectory-class
  membership — not single-point severity — carries the predictive
  signal. **Together these establish that variable-window,
  lag-structured, trajectory-based escalation prediction is a validated
  methodology in psychiatry generally** — but none integrate this with
  LLM narrative understanding, a knowledge graph, or symbolic
  verification, and none are OCD-specific (see Part E, point 5).
  Separately, Kadirvelu et al. (2026, *JMIR*) provide the closest
  methodological precedent for Layer 1.5's *rigidity embedding*
  specifically (not just temporal escalation): a two-stage
  **contrastive pretraining (triplet margin loss) + supervised
  fine-tuning** framework, applied to smartphone active+passive
  behavioral data in adolescents, outperforms both a no-pretraining
  baseline and CatBoost (p<0.001) at predicting risk outcomes including
  suicidal ideation (balanced accuracy 0.77). This validates
  contrastive learning as a real-world-tested strategy for stabilizing
  psychological/behavioral representations before downstream
  prediction — directly analogous to `rigidity_embedding.py`'s
  contrastive fine-tuning on (rigid, flexible) narrative pairs — though
  applied to multimodal sensor data rather than narrative text, and
  using SHAP (not a self-explanatory design) for interpretability.

**Limitation:** Opaque reasoning (black-box), no semantic
understanding of unstructured narrative text, no symbolic
verification against guidelines.

---

### Part C: Large Language Models in Clinical Diagnosis (2023–2024)

- **CPLLM: Clinical Prediction with LLMs** [11]: Shoham & Rappoport
  (2023) — LLMs perform clinical diagnosis prediction directly from
  patient data. First major demonstration of LLM clinical capability.
  No confidence calibration, no safety verification.
- **LLM + Medical Knowledge Grounding** [12]: Gao et al. (2023) —
  grounding LLM predictions with medical knowledge improves diagnosis
  accuracy. First hybrid LLM+knowledge approach, but grounding is
  applied *post-hoc* (after the LLM commits to an output), not
  *pre-generation*.
- **Domain-Specific LLM Evaluation** [13, 14]: Koga et al. (2024)
  evaluate ChatGPT/Bard on neurodegenerative differential diagnosis;
  Warrier et al. (2024) evaluate LLMs in otolaryngology. Both show
  domain-specific reasoning gaps. **No mental-health-specific
  evaluation in this line of work.**
- **Hallucination & Safety Risk Quantified** [Nature npj Digital
  Medicine 2025a, 2025b]: Recent benchmarks show **13.3% performance
  drop in high-risk clinical scenarios**, safety scores (54.7%)
  substantially below general performance (62.3%); medical text
  summarization hallucination rate ≈1.47%. Quantitative confirmation
  that LLM-only clinical deployment is unsafe without a verification
  layer.
- **Mental-Health-Specific Trustworthiness** [TrustMH-Bench 2025]:
  First *multidimensional* benchmark evaluating LLM trustworthiness
  across eight axes in mental health contexts (anxiety, depression,
  suicidality, general MH). Reveals **domain-specific reasoning
  failures in psychiatric contexts** — evidence that generic medical
  LLM competence does not transfer reliably to mental health. Notably,
  TrustMH-Bench found that domain-specific fine-tuning (models trained
  explicitly on mental health data) performs *worse* than general models
  on crisis identification and escalation decisions: *"Domain-specific
  fine-tuning does not appear to improve performance and may introduce
  higher variance, reducing decision stability in critical scenarios"*
  (§ G.2). This empirically motivates Nausica's approach: fine-tuning
  alone (Layer 1's distortion classifier) is insufficient for clinical
  safety; an independent deterministic verification layer (Layer 3) is
  necessary to catch where domain-specific models fail.
- **Comprehensive Trustworthiness Survey** [2025, arXiv:2502.15871]:
  Surveys the state of the art; identifies interpretability,
  hallucination, and consistency as the three unresolved pillars —
  exactly the three pillars Nausica's four layers target.

**Limitation:** LLMs lack structured domain knowledge, hallucinate,
contradict themselves, and — critically, per Part E below — cannot be
trusted to reliably obey safety instructions given only as prompts.

---

### Part D: Neuro-Symbolic Integration (2001–2025)

**Logical Neural Networks (LNNs)** and related work formally combine
neural learning with symbolic logic:

- **Logical Neural Networks Foundation** [15]: Riegel et al. (2020) —
  integration of neural learning with first-order logic. Proves
  neuro-symbolic reasoning is viable, with learnable weights carrying
  logical semantics.
- **Fuzzy Logic Foundations** [16]: Esteva & Godo (2001) — formal
  basis (t-norms) for reasoning under uncertainty, applicable to
  clinical knowledge where certainty is rare.
- **Differentiable Logical Rule Learning** [17]: Yang, Yang & Cohen
  (2017) — logical rules learned end-to-end via backpropagation.
  Bridges pure-neural and pure-symbolic; a model for Nausica's
  Layer 1.5 ↔ Layer 3 integration.
- **LNNs Applied to Text Reasoning** [21, 22]: Jiang et al. (2021,
  ACL) and Lu et al. (2022) apply LNNs to entity linking, showing
  neuro-symbolic methods scale to NLP tasks, not just tabular data.
- **LNNs for Knowledge Base Completion** [23]: Sen et al. (2022,
  EMNLP) combine LNNs with embeddings *and* rules — direct precedent
  for combining Layer 1.5 (embeddings/NN) with Layer 2/3
  (KG/rules) as complementary, not competing, signals.
- **Neuro-Symbolic Clinical Decision Support** [PMC12150699]: LNNs
  applied to diabetes diagnosis (Pima Indian dataset [18, 19, 20])
  show that transparent feature weights align with known medical
  knowledge (glucose, BMI), outperforming black-box interpretability.
  **Explicitly stated limitations**: tabular/structured data only, no
  unstructured narrative support, no real-world clinical validation
  ("proof-of-concept... generalizability... requires further
  exploration"), single condition only, LLMs explicitly noted as
  complementary (needed for unstructured text) rather than
  substitutable.

**Key recognition:** Neuro-symbolic reasoning is an established field
in clinical AI. Nausica's gap is *not* "neuro-symbolic doesn't exist,"
but the specific unaddressed combination detailed in Part E.

---

### Part E: Why Hybrid LLM+KG Systems Lack Independent Verification (2023–2026)

Prior hybrid clinical LLM+KG systems — MindMap [Wen et al., ACL 2024],
medIKAL [Jia et al., arXiv 2406.14326, 2024], CliCARE [2024], MedRAG
[Zhao et al., WWW 2025] — employ different integration strategies, but
all share a critical limitation: **no independent, deterministic layer
verifies the final output against declarative facts and safety rules**.

MindMap and MedRAG use a retrieve-then-generate pattern (knowledge
retrieved *before* LLM generation):

```
Patient input → KG Evidence Retrieval → LLM generation
                                        (using context)
                                           ↓
                                        Output
                                        (LLM is final arbiter)
```

medIKAL, CliCARE, and post-hoc hybrid systems use generate-then-filter:

```
Patient input → LLM generation → KG/Rules consultation → Output
                 ↑ COMMITTED     ↑ POST-HOC CHECK (too late)
```

In *both* patterns, the LLM makes the final decision. Recent evidence
sharpens why this fails, and why prompt-level fixes are insufficient:

1. **Even with retrieval, the LLM remains the final arbiter** [MindMap,
   MedRAG design; medIKAL limitations]: Knowledge retrieved before
   generation provides context, but the LLM can still ignore, misweight,
   or misinterpret it. medIKAL explicitly notes: *"LLMs tend to overly
   rely on the provided context... making it easy to be misled by
   incorrect knowledge"* (Limitations). MindMap and MedRAG motivate
   their work by showing that even *with* KG retrieval, heuristic
   diagnosis systems produce vague or clinically indefensible outputs.
   No independent rule-based verifier can reject an LLM output that
   violates guideline compliance or contains internal contradictions.

2. **Domain-specific fine-tuning is insufficient for clinical safety**
   [TrustMH-Bench 2025, § G.2]: Models explicitly fine-tuned on mental
   health data (SoulChat2, Simpsybot) perform *worse* than general-purpose
   LLMs on crisis detection and escalation decisions. This is a direct
   empirical finding that training-time domain adaptation — even with
   clinically curated data — cannot guarantee that a neural model will
   make safe, guideline-compliant decisions under all real-world
   conditions. Nausica's Layer 1 (distortion classifier, domain-adapted)
   must therefore be paired with Layer 3 (deterministic verification) to
   catch failure modes that arise even after careful fine-tuning.

3. **Instruction hierarchies are not reliably enforced — even by
   state-of-the-art models** [Geng et al., AAAI 2026, "Control
   Illusion"]: across six frontier LLMs (GPT-4o, Claude 3.5 Sonnet,
   Llama-70B, etc.), Primary Obedience Rate — how often a model
   follows a system-level constraint when it conflicts with user
   input — falls from **74.8–90.8%** (constraint presented alone) to
   just **9.6–45.8%** (constraint in conflict), even with explicit
   priority emphasis ("you must always follow this"). Best case
   (GPT-4o, simple conflicts): 63.8%. Worse still: models are *more*
   swayed by implicit **social framing** (authority, expertise,
   consensus — e.g., "per a peer-reviewed Nature study") than by
   explicit system/user role separation. **This is decisive evidence
   that a clinical AI system cannot rely on prompt-level policy alone
   to guarantee safety compliance** — the LLM may simply not obey it
   when patient input conflicts with the intended clinical constraint.
   This is precisely why Nausica's Layer 3 is a deterministic,
   independent verifier rather than a "better prompt."

4. **Pre-generation structural constraints are technically viable but
   unapplied to clinical semantics** [Bastan et al., ACL 2023,
   "NeuroStructural Decoding"; Geng et al., EMNLP 2023,
   "Grammar-Constrained Decoding"; "Thinking Before Constraining,"
   2025]: structural/grammar constraints enforced *during* generation
   (not post-hoc) measurably reduce entity/relation errors, including
   in a biomedical mechanism-generation task structurally analogous to
   Nausica's reasoning chains (SuMe: ROUGE-L 43.3→44.1, fewer
   "missing entity / wrong relation" errors). But existing work
   enforces *syntactic* structure (subject–verb–object), not
   *clinical semantic* structure (obsession → distortion → protocol →
   contraindication) — the gap Nausica's Layer 2 KG fills.

5. **No confidence gating**: none of the above systems signal
   uncertainty *backward* to influence how much scrutiny a
   recommendation receives. DIPOLE [8] and multi-layer classifiers
   [4, 7] show ensembling helps, but no clinical LLM+symbolic hybrid
   uses a neural confidence signal to modulate downstream
   verification effort.

6. **No temporal escalation prediction *integrated with* LLM+symbolic
   reasoning**: classical and LLM diagnostic systems alike [2, 3, 6,
   11–14] predict single-point diagnosis, not trajectory. This is not
   because escalation prediction is unsolved in psychiatry generally —
   Su et al. (2020) predict suicide risk across variable windows
   (AUC 0.81–0.86) and Meyer et al. (2022) use DTVEM to identify
   specific lag windows (1–8, 1–12 days) at which sleep disturbance
   predicts psychosis deterioration from smartphone daily-sampling
   data (see Part B). The actual gap is narrower and more specific:
   **no system combines lag-structured/variable-window escalation
   prediction with narrative LLM understanding, a symbolic knowledge
   base, and rule verification, in an OCD-specific instantiation.**
   Su et al. and Meyer et al. operate on structured EHR fields or
   single-item daily sleep/symptom ratings — not unstructured patient
   narrative — and neither feeds its prediction into a downstream
   verification layer; the signal terminates at a risk score. Nausica's
   Layer 1.5 must justify, empirically, that its transformer's
   escalation signal (trained on distortion-labeled narrative
   sequences) is comparably reliable to these structured-data
   precedents, and that gating Layer 3 scrutiny on it is Nausica's
   specific contribution beyond producing the score itself.

7. **Not validated in real psychiatric workflows**: prototypes are
   tested on curated benchmarks (Pima diabetes [18–20], synthetic
   cases) or narrow specialties (neurology [13], otolaryngology [14]).
   No mental-health-specific, real-clinician-workflow validation
   exists for a neuro-symbolic LLM system.

8. **"Interpretability" claims in prior LLM+KG hybrids are rarely
   distinguished from plausibility** [Jacovi & Goldberg, ACL 2020;
   Lyu et al., *Computational Linguistics* 2024]: the NLP
   interpretability literature draws a sharp, foundational distinction
   between **plausibility** (does an explanation seem convincing to a
   human?) and **faithfulness** (does it accurately reflect the
   model's actual decision process?). Lyu et al.'s survey of 110+
   explanation methods shows most LLM explanations — including
   chain-of-thought — are post-hoc narratives generated *after* the
   answer, and are frequently plausible but unfaithful. None of the
   clinical LLM+KG systems in this gap analysis (MindMap, medIKAL,
   CliCARE) evaluate their explanations against this faithfulness
   standard; "interpretable" in that literature means "produces a
   textual explanation," not "the explanation is the actual
   computation." This is the formal grounding Nausica's IFS metric
   uses (see Part F). This concern is not theoretical: post-hoc
   explanation methods in clinical ML (LIME, SHAP — the field's
   default toolkit [Ahmed et al., *IEEE Access* 2024]) have been shown
   to be **adversarially foolable** — Slack et al. (2020) demonstrate
   that biased classifiers can be constructed to systematically deceive
   LIME/SHAP into producing innocuous-looking explanations for
   discriminatory decisions. A post-hoc explanation is an
   *approximation* of a black box, not a guarantee about it.

9. **Faithfulness is one axis of three, and modular explainer/predictor
   splits *reduce* faithfulness** [Yeo et al., NAACL Findings 2024,
   "How Interpretable are Reasoning Explanations from Prompting Large
   Language Models?"]: extending Jacovi & Goldberg's single
   faithfulness axis, Yeo et al. formalize **three** measurable
   interpretability properties — faithfulness (does the explanation
   reflect the true decision process?), robustness (does it survive
   paraphrase?), and utility (does it help a downstream learner predict
   the answer, measured via Leakage-Adjusted Simulatability, LAS
   [Hase et al. 2020]) — each with concrete perturbation tests:
   paraphrasing, adversarial mistake-insertion, and counterfactual
   question-editing. Critically, their motivating experiment (built on
   the PINTO framework [Wang et al. 2022]) shows that a **modular**
   explainer-then-predictor pipeline (one model generates the
   explanation, a separate model conditions on it to predict) is
   measurably *less* faithful and *less* useful than a **single** model
   that generates reasoning and answer jointly — because a separate
   predictor is not causally bound to the explainer's output. **This
   raises an internal design question Nausica must answer explicitly**:
   Layer 3 is architecturally separate from Layer 1 — is it the same
   "modular" anti-pattern? No: Yeo et al.'s finding concerns a module
   that *generates an explanation for* another module's decision (the
   explanation is decorative). Layer 3 does not explain Layer 1's
   decision — it independently *verifies* Layer 1's candidate against
   declarative facts and deterministic rules, producing a pass/fail/flag
   outcome. The reasoning chain is not a post-hoc rationalization of
   Layer 1's output; it is the trace of Layer 3's own, separate
   computation. Nausica's IFS must still be validated per-layer to
   confirm this distinction holds in practice (Phase 11, Q2).

10. **Hybrid neural (LLM) + deterministic evaluation is a validated
   pattern outside clinical NLP, but untested for clinical safety
   verification** [Anghel et al., *Informatics* 2025, "Multi-Model
   Dialectical Evaluation of LLM Reasoning Chains"]: Dialectical Agent
   combines two independent LLM evaluators (scoring clarity, coherence,
   originality, dialecticality) with a **separate rule-based semantic
   analyzer** (regex/lexicon-based, deterministic) that detects
   rhetorical anomalies and ethical values, storing the full reasoning
   trace in a graph database (Neo4j) for structured, queryable
   inspection. Their finding — rubric-based LLM scoring *alone* misses
   qualitative failures that only the deterministic symbolic layer
   catches — is direct empirical precedent for pairing neural
   confidence (Layer 1.5) with independent symbolic verification
   (Layer 3), and for storing verifiable reasoning chains in a queryable
   graph structure (Layer 2). Runs entirely on local Ollama models, the
   same deployment posture as Nausica. Limitation: general-purpose
   argumentation (10 prompts, single-turn, no clinical domain, no safety
   stakes) — Nausica extends this pattern to a safety-critical,
   multi-turn, OCD-specific setting.

---

### Part F: Nausica's Four-Layer Solution

We propose **Neuro-Symbolic Clinical Reasoning (NSCR)**: reversing the
timing (constrain *before* generation, verify *independently* after)
and adding neural confidence gating + temporal prediction:

```
PRE-GENERATION POLICY (Fable: shapes technique selection BEFORE the LLM generates)
   ↓
Layer 1: Neural LLM — semantic understanding of patient narrative
Layer 1.5: Predictive NNs — temporal escalation + rigidity confidence gating
Layer 2: Knowledge Graph — declarative clinical facts (OCD-specific)
Layer 3: Symbolic Rules — INDEPENDENT deterministic verification (not a prompt)
Layer 4: Real-world workflow — Obsidian pilot, clinician approval gate
```

**Specific gaps filled, each tied to the evidence above:**

1. **Pre-generation policy, backed by independent verification, not
   prompt-only control** (Fable + Layer 3): Unlike post-hoc grounding
   [12] and unlike relying on instruction hierarchies that empirically
   fail under conflict [Geng et al. AAAI 2026], Layer 3 is a
   deterministic rules engine that gates output *regardless of whether
   the LLM "obeyed" its prompt*.

2. **Predictive neural confidence** (Layer 1.5): temporal CFI
   transformer [extending DIPOLE's attention-based temporal modeling,
   8] predicts escalation; rigidity embedding scores cognitive
   inflexibility. Design of the escalation signal is grounded in two
   psychiatric precedents: variable-window prediction [Su et al. 2020 —
   0–365 day horizons, sequential feature selection] and lag-structured
   modeling [Meyer et al. 2022 — DTVEM, 1–8/1–12 day lags from daily
   digital sampling]. Unlike those systems, Nausica's signal derives
   from unstructured narrative (not structured EHR fields or single-item
   ratings) and feeds forward into symbolic verification rather than
   terminating at a risk score. These signals gate Layer 3 scrutiny —
   low confidence triggers additional rule checks. **Honest risk to
   flag:** Feusner et al. (2015, *Frontiers in Psychiatry*) — the first
   graph-theory rsfMRI study of CBT-relapse prediction in OCD (n=17,
   12-month follow-up) — found that pre-treatment brain network
   connectivity (small-worldness, clustering coefficient; adjusted
   R²=0.64, P=0.004) predicted relapse, while **psychometric and
   neurocognitive self-report measures (YBOCS, HAMA, MADRS, Stroop)
   did not**. This is direct evidence, in OCD specifically, that
   self-report/language-derived signals have historically
   underperformed structural biomarkers at relapse prediction. Nausica
   has no access to neuroimaging and must derive its escalation signal
   from narrative text — this precedent is a reason for caution, not
   just optimism, about Layer 1.5's ceiling, and should be treated as
   an explicit empirical question in Phase 11 (Q3) rather than assumed
   away.

3. **OCD-specific symbolic knowledge** (Layer 2): responding directly
   to TrustMH-Bench's finding that generic medical LLM competence does
   not transfer to psychiatric reasoning — obsessions, ERP protocols,
   and contraindications are encoded as declarative facts, distinct
   from Layer 3's procedural rules (see invariant below).

4. **Structural/semantic constraint enforcement during generation**
   (Layer 1 + Layer 2 interface): extending the *technique* validated
   by NeuroStructural Decoding [ACL 2023] — enforcing relational
   structure during decoding, not after — from syntactic roles to
   clinical semantic roles (distortion → technique → protocol).

5. **Formal interpretability metric** (IFS), grounded in the
   faithfulness literature [Jacovi & Goldberg, ACL 2020; Lyu et al.,
   CL 2024; Yeo et al., NAACL Findings 2024]: reasoning chains are
   **self-explanatory by construction** — the explanation IS the
   computational trace (LLM detection → NN confidence → KG lookup →
   rule verification), not a post-hoc narrative approximating a
   black-box decision (unlike LIME/SHAP, which are approximations by
   design and adversarially foolable [Slack et al. 2020]). Following
   Yeo et al.'s three-axis operationalization, IFS is not a single
   number but three testable properties, each with a concrete
   perturbation protocol adapted to Nausica's reasoning chain:
   - **Faithfulness**: (a) *necessity* — if a step (e.g., a specific KG
     fact or triggered rule) is removed, does the recommendation
     change? (b) *mistake-insertion* — if a step's stated evidence is
     corrupted (e.g., swap the queried obsession type), does the
     recommendation change accordingly? A faithful chain must fail to
     produce the same output under corruption.
   - **Robustness**: does the recommendation and reasoning chain remain
     stable under paraphrase of the patient's input text (same
     clinical content, different wording)?
   - **Utility**: does exposing the reasoning chain to a held-out
     evaluator (clinician or LLM-judge) measurably improve their
     ability to predict/validate the correct recommendation, versus
     seeing the recommendation alone? (Simulatability, adapted from
     LAS [Hase et al. 2020].)
   This directly addresses gaps 7–8 above — prior clinical LLM+KG
   systems claim "interpretability" without this distinction, and
   Nausica's per-layer separation (Layer 1 generates, Layer 3
   independently verifies) is explicitly tested against the
   modular-explainer failure mode Yeo et al. identify, not merely
   assumed safe from it.

6. **Real clinical workflow validation** (Layer 4): Obsidian plugin
   with clinician-in-the-loop approval gate — closing the
   real-world-validation gap common to all systems in Parts B–D.

**Layer 2 / Layer 3 invariant** (resolves prior redundancy risk):
Layer 2 stores only *declarative facts* ("contamination fear is
treated with graduated ERP exposure"). Layer 3 applies *procedural
inference* over those facts plus patient state and confidence signals
("given this patient's history and current rigidity, is this
recommendation safe *right now*?"). Facts don't change per patient;
rule outcomes do.

**That combination — LLM semantic understanding + independent
symbolic verification + neural temporal/confidence gating +
OCD-specific structured knowledge + real clinical workflow — is the
research opportunity.**

---

## 2. Why OCD as the Case Study

OCD is not the research focus — the architecture is — but it is the
deliberately chosen validation domain: (i) **clear diagnostic
criteria** (DSM-5); (ii) **standardized treatment protocols** (ERP/CBT
guidelines are explicit and published, giving Layer 3 something
concrete to verify against); (iii) **rich clinical narratives**
(obsessions are linguistically complex, stress-testing Layer 1); (iv)
**severe unmet need** (1–2% global prevalence, 8–17 year average
diagnostic delay, ERP therapist shortage acute in LATAM, and — per
TrustMH-Bench — generic mental-health LLM competence does not
transfer to OCD reasoning); and (v) it is **specific enough to be
defensible, general enough to transfer** — the same architecture,
re-instantiated with a different KG/rule set, extends to depression
maintenance and panic disorder (adjacent niches analyzed in
`NICHE_ANALYSIS.md`); and (vi) **a documented, clinically consequential
need for longitudinal course-tracking**, which is the concrete clinical
justification for Layer 1.5's escalation-prediction design (Part B,
Part F point 2). Marcks et al. (2011, *Comprehensive Psychiatry*), the
longest prospective naturalistic study of OCD course to date (15-year
follow-up, HARP cohort, n=113), show OCD has a genuinely
chronic-relapsing trajectory that standard annual/biannual clinical
visits are poorly suited to track: remission probability is only .16
at year 1, rising slowly to .42 at year 15, with comorbid depression
cutting the 15-year remission rate from 51% to 20%. Klein
Hofmeijer-Sevink et al. (2018, *Canadian Journal of Psychiatry*, NESDA
cohort, n=2125) independently show that subclinical obsessive-compulsive
*symptoms* (not just full OCD) function as a **course specifier** —
predicting first onset (OR 5.79), relapse (OR 2.31), and persistence in
comorbid anxiety/depression (OR 4.42) over a 2-year window — yet are
"easily missed in clinical practice" because patients rarely
self-report them unprompted. Together, these establish (a) that OCD's
course genuinely requires fine-grained longitudinal tracking to
manage, not just point-in-time diagnosis, and (b) that the symptoms
driving that course are specifically the kind clinicians under-detect
without structured, continuous instrumentation — the exact gap
Nausica's Obsidian-based Layer 4 (continuous patient narrative capture)
and Layer 1.5 (escalation prediction) are positioned to fill.

## 3. Primary Research Questions

| # | Question (one line) | Key metric / success criterion |
|---|---|---|
| **Q1** | Does NSCR produce more interpretable recommendations than an LLM alone? | Interpretability Fidelity Score: +25% over LLM-only baseline (with explicit CoT prompting for fair comparison) |
| **Q2** | Do the knowledge graph and symbolic rules reduce inconsistency and guarantee guideline compliance? | Consistency > 95%; guideline compliance > 99% against an independently authored expert checklist |
| **Q3** | Do the predictive neural layers improve confidence calibration and escalation detection? | ECE < 0.10; escalation AUROC > 0.75 vs. persistence baseline |
| **Q4** | What technical properties characterize the chosen knowledge representation (networkx)? | Query latency, edge expressivity, maintenance footprint — technical ablation |
| **Q5** | Does the architecture work in a real clinical workflow? | Usability smoke-test with 2–3 clinicians (SUS score); *not* an efficacy claim |

*(Clinician-rated Q1, expert-panel Q4, and patient-efficacy Q5 are
Phase 12+ work, contingent on IRB approval — see
`IMPLEMENTATION_PLAN.md`.)*

## 4. Scholarship Pitch Statement

> **We propose a four-layer neuro-symbolic architecture — LLM
> understanding, neural confidence prediction, knowledge-graph
> reasoning, and independent symbolic verification — that makes
> clinical AI recommendations explicit and auditable, instantiated on
> OCD as the validation domain, to answer whether such integration
> measurably improves interpretability (Q1), consistency and
> guideline compliance (Q2), and confidence calibration (Q3). If
> successful, this establishes a generalizable, formally evaluable
> methodology for interpretable clinical decision support — applicable
> to OCD today, depression and panic tomorrow, and guideline-driven
> medicine beyond.**

---

## References

### Classical Symbolic (1988–2001)

[1] Lucas, P. (1997). Symbolic diagnosis and its formalisation. *The
Knowledge Engineering Review*, 12(2), 109–46.

[2] Huang, G. M., Huang, K. Y., Lee, T. Y., & Weng, J. T. Y. (2015). An
interpretable rule-based diagnostic classification of diabetic
nephropathy among type 2 diabetes patients. *BMC Bioinformatics*, 16,
1–10.

[3] Choubey, D. K., Paul, S., & Dhandhenia, V. K. (2017). Rule based
diagnosis system for diabetes. *An International Journal of Medical
Sciences*, 28(12), 5196–208.

[Seitinger 2014] Seitinger, A., Fehre, K., Adlassnig, K.-P.,
Rappelsberger, A., Wurm, E., Aberer, E., & Binder, M. (2014). An
Arden-Syntax-Based Clinical Decision Support Framework for Medical
Guidelines—Lyme Borreliosis as an Example. *eHealth2014*, 125–132.
doi:10.3233/978-1-61499-397-1-125

[Boxwala 2004] Boxwala, A. A., Peleg, M., Tu, S., et al. (2004). GLIF3:
A representation format for sharable computer-interpretable clinical
practice guidelines. *Journal of Biomedical Informatics*, 37(3),
147–161.

[Peleg 2003] Peleg, M., Tu, S., Bury, J., et al. (2003). Comparing
computer-interpretable guideline models: a case-study approach.
*JAMIA*, 10(1), 52–66.

### Multi-Layer Neural (2016–2024)

[4] Bashir, S., Qamar, U., Khan, F. H., & Naseem, L. (2016). HMV: A
medical decision support framework using multi-layer classifiers for
disease prediction. *Journal of Computational Science*, 13, 10–25.

[5] Joloudari, J. H., Saadatfar, H., Dehzangi, A., & Shamshirband, S.
(2019). Computer-aided decision-making for predicting liver disease
using PSO-based optimized SVM with feature selection. *Informatics in
Medicine Unlocked*, 17, 100255.

[6] Fitriyani, N. L., Syafrudin, M., Alfian, G., & Rhee, J. (2020).
HDPM: An effective heart disease prediction model for a clinical
decision support system. *IEEE Access*, 8, 133034–50.

[7] Rani, P., Kumar, R., Ahmed, N. M. S., & Jain, A. (2021). A decision
support system for heart disease prediction based upon machine
learning. *Journal of Reliable Intelligent Environments*, 7(3),
263–75.

[8] Ma, F., Chitta, R., Zhou, J., You, Q., Sun, T., & Gao, J. (2017).
DIPOLE: Diagnosis prediction in healthcare via attention-based
bidirectional recurrent neural networks. *KDD 2017*, 1903–11.

[9] Tufail, A. B., Ma, Y. K., Kaabar, M. K., et al. (2021). Deep
learning in cancer diagnosis and prognosis prediction: a minireview.
*Computational and Mathematical Methods in Medicine*, 2021, 9025470.

[10] Liu, T., Siegel, E., & Shen, D. (2022). Deep learning and medical
image analysis for COVID-19 diagnosis and prediction. *Annual Review
of Biomedical Engineering*, 24(1), 179–201.

### LLMs in Clinical Diagnosis (2023–2025)

[11] Shoham, O. B., & Rappoport, N. (2023). CPLLM: Clinical prediction
with large language models. *PLOS Digital Medicine*.
doi:10.1371/journal.pdig.0000680

[12] Gao, Y., Li, R., Croxford, E., et al. (2023). Large language
models and medical knowledge grounding for diagnosis prediction.
*medRxiv*, 2023–11.

[13] Koga, S., Martin, N. B., & Dickson, D. W. (2024). Evaluating the
performance of large language models: ChatGPT and Google Bard in
generating differential diagnoses in clinicopathological conferences
of neurodegenerative disorders. *Brain Pathology*, 34(3), e13207.

[14] Warrier, A., Singh, R., Haleem, A., Zaki, H., & Eloy, J. A.
(2024). The comparative diagnostic capability of large language models
in otolaryngology. *The Laryngoscope*.

[Nature npj 2025a] A framework to assess clinical safety and
hallucination rates of LLMs for medical text summarisation. *npj
Digital Medicine* (2025).

[Nature npj 2025b] A novel evaluation benchmark for medical LLMs
illuminating safety and effectiveness in clinical domains. *npj
Digital Medicine* (2025). — 13.3% performance drop in high-risk
scenarios; safety 54.7% vs. overall 62.3%.

[TrustMH-Bench 2025] A Comprehensive Benchmark for Evaluating the
Trustworthiness of Large Language Models in Mental Health. arXiv:
2603.03047.

[Trustworthiness Survey 2025] A Comprehensive Survey on the
Trustworthiness of Large Language Models in Healthcare. arXiv:
2502.15871.

### Neuro-Symbolic Integration (2001–2025)

[15] Riegel, R., Gray, A., Luus, F., et al. (2020). Logical neural
networks. arXiv:2006.13155.

[16] Esteva, F., & Godo, L. (2001). Monoidal t-norm based logic:
towards a logic for left-continuous t-norms. *Fuzzy Sets and Systems*,
124(3), 271–88.

[17] Yang, F., Yang, Z., & Cohen, W. W. (2017). Differentiable
learning of logical rules for knowledge base reasoning. *NeurIPS
2017*, 30.

[21] Jiang, H., Gurajada, S., Lu, Q., et al. (2021). LNN-EL: A
Neuro-Symbolic Approach to Short-text Entity Linking. *ACL 2021*,
775–87.

[22] Lu, Q., Gurajada, S., Sen, P., et al. (2022). Cross-lingual
short-text entity linking: Generating features for neuro-symbolic
methods. *4th Workshop on Data Science with Human-in-the-Loop*, 8–14.

[23] Sen, P., Carvalho, B. W., Abdelaziz, I., et al. (2022). Logical
neural networks for knowledge base completion with embeddings &
rules. *EMNLP 2022*, 3863–75.

[PMC12150699] Logical Neural Networks for Clinical Decision Support: A
Neuro-Symbolic Approach [diabetes case study]. *PMC*.

### Clinical Datasets & Context

[18] Chang, V., Bailey, J., Xu, Q. A., & Sun, Z. (2023). Pima Indians
diabetes mellitus classification based on machine learning (ML)
algorithms. *Neural Computing and Applications*, 35(22), 16157–73.

[19] Smith, J. W., Everhart, J. E., Dickson, W., Knowler, W. C., &
Johannes, R. S. (1988). Using the ADAP learning algorithm to forecast
the onset of diabetes mellitus. *Symposium on Computer Application in
Medical Care*, 261.

[20] Schulz, L. O., Bennett, P. H., Ravussin, E., et al. (2006).
Effects of traditional and western environments on prevalence of type
2 diabetes in Pima Indians in Mexico and the US. *Diabetes Care*,
29(8), 1866–71.

### Pre-Generation Policy, Constrained Decoding & Instruction Reliability (2023–2026)

[Henneking 2025] Henneking, C.-L., et al. (2025). Decoding Human
Preferences in Alignment: An Improved Approach to Inverse
Constitutional AI. arXiv:2501.17112. — Extracts explicit, interpretable
principles ("constitutions") from preference data, refining
Constitutional AI's rule-based alignment paradigm.

[Geng 2023 EMNLP] Geng, S., Josifoski, M., Peyrard, M., & West, R.
(2023). Grammar-Constrained Decoding for Structured NLP Tasks without
Finetuning. *EMNLP 2023*, 10932–10952. — Formal grammars enforce
output structure during generation without task-specific fine-tuning.

[Bastan 2023 ACL] Bastan, M., Surdeanu, M., & Balasubramanian, N.
(2023). NeuroStructural Decoding: Neural Text Generation with
Structural Constraints. *ACL 2023*, Vol. 1, 9496–9510. — Extends
NeuroLogic Decoding to syntactic (subject-verb-object) constraints
enforced during beam search; demonstrated on a biomedical
mechanism-generation task (SuMe) structurally analogous to clinical
reasoning-chain generation. Constraints applied *during* decoding, not
post-hoc; reduces missing-entity and wrong-relation errors.

["Thinking Before Constraining" 2025] Thinking Before Constraining: A
Unified Decoding Framework for Large Language Models. arXiv:2601.07525.
— Unconstrained reasoning phase followed by trigger-activated
structured decoding; +27% accuracy over naive constrained generation.
Premature constraint application degrades reasoning quality.

[BioMed-VITAL, NeurIPS 2024] Biomedical Visual Instruction Tuning with
Clinician Preference Alignment. *NeurIPS 2024, Datasets & Benchmarks
Track*. — Distills clinician preferences into a rating function for
training-data selection (two-stage: clinician-guided generation +
clinician/policy-guided selection). Precedent for clinician-preference
alignment in biomedical AI; Nausica's Layer 4 extends this concept from
*training-time* data curation to *runtime* per-recommendation approval.

[Geng et al. 2026, AAAI, "Control Illusion"] Geng, Y., Li, H., Mu, H.,
Han, X., Baldwin, T., Abend, O., Hovy, E., & Frermann, L. (2026).
Control Illusion: The Failure of Instruction Hierarchies in Large
Language Models. *AAAI-26*. — **Critical finding**: six state-of-the-art
LLMs (GPT-4o, Claude 3.5 Sonnet, Llama-70B, etc.) fail to reliably
enforce system-level constraints under conflict with user input;
Primary Obedience Rate falls from 74.8–90.8% (isolated) to 9.6–45.8%
(conflicting), even with explicit priority emphasis. Implicit social
framing (authority, expertise, consensus) sways models more than
explicit system/user roles. Directly justifies why Nausica's Layer 3
is an independent, deterministic verifier rather than a prompt-level
safety instruction.

### Faithfulness & Interpretability Metrics (2020–2024)

[Jacovi & Goldberg 2020] Jacovi, A., & Goldberg, Y. (2020). Towards
Faithfully Interpretable NLP Systems: How Should We Define and
Evaluate Faithfulness? *Proceedings of the 58th Annual Meeting of the
ACL*, 4198–4205. — **Foundational**: establishes the distinction
between *plausibility* (does an explanation seem convincing?) and
*faithfulness* (does it reflect the model's actual decision process?).
Formal grounding for IFS.

[Lyu et al. 2024] Lyu, Q., Apidianaki, M., & Callison-Burch, C. (2024).
Towards Faithful Model Explanation in NLP: A Survey. *Computational
Linguistics*, 50(2), 657–723. — Surveys 110+ explanation methods across
five families (similarity-based, model-internal analysis,
backpropagation-based, counterfactual intervention, self-explanatory
models). Nausica's reasoning chains fall in the highest-faithfulness
category (self-explanatory: the explanation is the computation, not an
approximation of it).

[Yeo et al. 2024] Yeo, W. J., Satapathy, R., Goh, R. S. M., & Cambria, E.
(2024). How Interpretable are Reasoning Explanations from Prompting
Large Language Models? *Findings of the Association for Computational
Linguistics: NAACL 2024*, 2148–2164. — **Key operationalization
source for IFS**: formalizes three testable interpretability axes
(faithfulness, robustness, utility) with concrete perturbation
protocols (paraphrase, mistake-insertion, counterfactual editing,
LAS-based simulatability). Also shows, via the PINTO framework [Wang
et al. 2022], that modular explainer→predictor pipelines are *less*
faithful than joint generation — a finding Nausica's Layer 1/Layer 3
separation must be explicitly tested against (see Part E, point 8).

[Slack et al. 2020] Slack, D., Hilgard, S., Jia, E., Singh, S., &
Lakkaraju, H. (2020). Fooling LIME and SHAP: Adversarial Attacks on
Post Hoc Explanation Methods. *Proceedings of the AAAI/ACM Conference
on AI, Ethics, and Society*, 180–186. — Demonstrates that biased
classifiers can be deliberately constructed to fool LIME/SHAP into
producing innocuous explanations, proving post-hoc explanation methods
are approximations, not guarantees. Motivates Nausica's self-explanatory
(non-post-hoc) design for Layer 3.

[Ahmed et al. 2024] Ahmed, S., Kaiser, M. S., Hossain, M. S., &
Andersson, K. (2024). A Comparative Analysis of LIME and SHAP
Interpreters With Explainable ML-Based Diabetes Predictions. *IEEE
Access*, 13, 37370–37388. — Confirms LIME/SHAP remain the default
post-hoc XAI toolkit in current clinical ML (tabular diabetes
prediction); documents their known instability, lack of ground-truth
validation, and disagreement between methods on the same prediction
— the specific failure mode Nausica's self-explanatory reasoning
chains are designed to avoid.

[Anghel et al. 2025] Anghel, C., Anghel, A. A., Pecheanu, E., Susnea,
I., Cocu, A., & Istrate, A. (2025). Multi-Model Dialectical Evaluation
of LLM Reasoning Chains: A Structured Framework with Dual Scoring
Agents. *Informatics*, 12(3), 76. — Architectural precedent for
Nausica's Layer 1.5/Layer 3 split: pairs independent LLM evaluators
(neural, rubric-based) with a separate deterministic rule-based
semantic analyzer, storing reasoning traces in a graph database
(Neo4j) for structured inspection. Runs on local Ollama models. Shows
rubric-only LLM scoring misses failures only the symbolic layer
catches. Limitation: general argumentation, not clinical, no safety
stakes, single-turn — Nausica extends this pattern to OCD-specific,
multi-turn, safety-critical reasoning.

[Zhang & Liu 2025] Zhang, C., & Liu, L. (2025). Machine Learning
Prediction Model for Medical Environment Comfort Based on SHAP and
LIME Interpretability Analysis. *Scientific Reports*, 15, 39269. —
Recent (2025) clinical-adjacent deployment of dual SHAP+LIME
interpretability with rigorous statistical validation (paired t-tests,
95% CIs) and an explicit ethical/deployment considerations section
(algorithmic transparency, false-positive/negative risk management,
computational performance benchmarking) — a structural template for
Nausica's own security/regulatory documentation and Phase 11
statistical reporting standards.

### Temporal Prediction & Escalation Detection in Psychiatry (2020–2026)

[Su et al. 2020] Su, C., Aseltine, R., Doshi, R., Chen, K., Rogers,
S. C., & Wang, F. (2020). Machine learning for suicide risk prediction
in children and adolescents with electronic health records.
*Translational Psychiatry*, 10, 413. — Predicts suicide risk from EHR
data across multiple prediction windows (0–365 days) using sequential
forward feature selection; AUC 0.81–0.86; shows predictor importance
varies by window length. Establishes variable-window escalation
prediction as a validated methodology in psychiatric risk modeling —
grounds the design of Nausica's Layer 1.5 temporal CFI transformer
(see Part B, Part E point 5, Part F point 2).

[Meyer et al. 2022] Meyer, N., Lok, R., Schmidt, C., et al. (2022).
The temporal dynamics of sleep disturbance and psychopathology in
psychosis: a digital sampling study. *Psychological Medicine*, 52(16),
3862–3870. — Smartphone daily-sampling study (Sleepsight app) using a
Differential Time-Varying Effect Model (DTVEM) to identify specific lag
windows (1–8, 1–12 days) at which sleep disturbance predicts psychosis
symptom deterioration, with negative affect as a significant mediator.
Closest methodological precedent to Nausica's Layer 1.5: digital,
fine-grained, lag-structured escalation modeling — but on single-item
daily ratings, not narrative text, and without downstream symbolic
verification.

[Chen et al. 2026] Chen, Y., et al. (2026). Life event trajectories and
suicidal ideation throughout adolescence: a study of the IMAGEN cohort.
*Lancet Psychiatry* (advance online). — Uses latent trajectory (finite
mixture) models to classify adolescent life-event exposure into risk
trajectories predictive of suicidal ideation; shows trajectory-class
membership, not single-point severity, carries predictive signal.
Secondary precedent for trajectory-based (rather than point-estimate)
framing of escalation risk.

[Kadirvelu et al. 2026] Kadirvelu, B., Bellido Bel, T., Freccero, A.,
Di Simplicio, M., Nicholls, D., & Faisal, A. A. (2026). Digital
Phenotyping for Adolescent Mental Health: Feasibility Study Using
Machine Learning to Predict Mental Health Risk From Active and Passive
Smartphone Data. *Journal of Medical Internet Research*, 28, e72501. —
Two-stage contrastive pretraining (triplet margin loss) + supervised
fine-tuning framework on 14-day smartphone active/passive data (103
adolescents), predicting SDQ risk, insomnia, suicidal ideation
(balanced accuracy 0.77), and eating-disorder risk; externally
validated (n=45). Closest real-world precedent for Layer 1.5's
contrastive rigidity embedding methodology (see Part B). Uses SHAP for
interpretability — reinforces that post-hoc explanation remains the
field default even in state-of-the-art digital phenotyping (cf. Slack
et al. 2020, Ahmed et al. 2024).

[Beckenstrom et al. 2026] Beckenstrom, A. C., et al. (2026). A digital
imagery-competing task intervention for reducing intrusive memories
after trauma (ICTI/GAINS-02): a randomised controlled trial. *Lancet
Psychiatry* (advance online). — Bayesian adaptive RCT design for a
brief, single-session digital intervention delivered by non-specialist
"digital navigators." Not a temporal-prediction paper, but a real-world
deployment precedent relevant to Layer 4 (Obsidian as clinician-adjacent
delivery instrument) and to Bayesian adaptive trial design for a future
Nausica pilot (Q5).

[Crawford et al. 2026] Crawford, M. J., et al. (2026). A brief
individual psychological intervention for people with probable
personality disorder (SPS trial): a randomised controlled trial.
*Lancet Psychiatry* (advance online). — Reports a **null result**: the
brief intervention showed no benefit over treatment as usual. Included
not for methodology but as a disclosure-standard precedent — reinforces
that Nausica's own validation reporting (Phase 12+) must be prepared to
report null or negative findings honestly, consistent with the
project's existing honest-reporting conventions.

### OCD Clinical Course & Comorbidity (2011–2018)

[Feusner et al. 2015] Feusner, J. D., Moody, T., Lai, T. M., Sheen, C.,
Khalsa, S., Brown, J., Levitt, J., Alger, J., & O'Neill, J. (2015).
Brain connectivity and prediction of relapse after cognitive-behavioral
therapy in obsessive-compulsive disorder. *Frontiers in Psychiatry*, 6,
74. — First graph-theory rsfMRI study of CBT-relapse prediction in OCD
(n=17, 12-month follow-up). Pre-treatment network connectivity
(small-worldness, clustering coefficient) predicted relapse (adjusted
R²=0.64, P=0.004); psychometric/neurocognitive self-report measures
(YBOCS, HAMA, MADRS, Stroop) did not. **Important counter-evidence**:
shows self-report/language-derived signals have underperformed
structural biomarkers at OCD relapse prediction specifically — a
caution for Layer 1.5's narrative-derived escalation signal, flagged
as an open empirical question rather than assumed away (see Part F,
point 2).

[Marcks et al. 2011] Marcks, B. A., Weisberg, R. B., Dyck, I., & Keller,
M. B. (2011). Longitudinal course of obsessive-compulsive disorder in
patients with anxiety disorders: a 15-year prospective follow-up study.
*Comprehensive Psychiatry*, 52(6), 670–677. — Longest prospective
naturalistic study of OCD course (HARP cohort, n=113, 15-year
follow-up). Remission probability .16 at year 1 rising to .42 at
year 15; comorbid MDD reduces 15-year remission from 51% to 20%.
Establishes OCD's genuinely chronic-relapsing, slow-moving course —
the epidemiological grounding for why longitudinal course-tracking
(vs. point-in-time diagnosis) is clinically necessary (see Section 2,
point vi).

[Klein Hofmeijer-Sevink et al. 2018] Klein Hofmeijer-Sevink, M.,
Batelaan, N. M., van Megen, H. J. G. M., van den Hout, M. A., Penninx,
B. W., van Balkom, A. J. L. M., & Cath, D. C. (2018). Presence and
Predictive Value of Obsessive-Compulsive Symptoms in Anxiety and
Depressive Disorders. *The Canadian Journal of Psychiatry*, 63(2),
85–93. — NESDA cohort (n=2125): subclinical obsessive-compulsive
symptoms predict first onset (OR 5.79), relapse (OR 2.31), and
persistence in comorbid anxiety/depression (OR 4.42) over 2 years, yet
are frequently unreported/undetected in clinical practice without
structured screening. Establishes OCS as a validated **course
specifier** — direct clinical justification for continuous,
structured symptom capture (Layer 4) feeding escalation prediction
(Layer 1.5).

---

*Scope note: this is a research prototype, not a medical device. All
distortion labels are LLM weak-labeled (no clinician ground truth at
scale); outputs are never framed as diagnosis or treatment. These
limitations are disclosed throughout the proposal and validation
documents.*
