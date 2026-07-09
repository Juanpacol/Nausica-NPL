# Neuro-Symbolic Clinical Reasoning Architecture for LLM-Based Decision Support

## Research Proposal for Doctoral Study

**Working Title:** Knowledge-Grounded Neuro-Symbolic Reasoning for Interpretable Clinical Decision Support: Design, Validation, and OCD Application

**Principal Investigator:** [Your Name]

**Date:** July 8, 2026

---

## 1. INTRODUCTION

### 1.1 The Core Problem

Large Language Models (LLMs) have demonstrated remarkable capabilities in natural language understanding and generation. However, their application to clinical settings faces a critical barrier: **interpretability and verifiability**. 

When an LLM recommends a treatment intervention, clinicians and regulators need to know:
- **Why** this recommendation was made
- **What evidence** supports it
- **Whether it complies** with clinical guidelines
- **How confident** the system is

Current LLM-based clinical systems operate as "black boxes"—they produce recommendations without explicable reasoning chains. This is incompatible with clinical standards of care.

### 1.2 The Research Gap

Two complementary approaches exist but remain largely separate:

1. **Neural approaches (LLMs):** Flexible, understand nuance, but opaque
2. **Symbolic approaches (Knowledge Graphs + Rules):** Interpretable, verifiable, but rigid

**The research opportunity:** Design and validate a **hybrid neuro-symbolic architecture** that combines:
- LLM flexibility (understanding complex clinical narratives)
- Neural network prediction (temporal dynamics, confidence scoring)
- Symbolic knowledge representation (explicit clinical reasoning)
- Formal rule verification (guideline compliance)

### 1.3 Why This Matters

This architecture is not specific to mental health. It is a **generalizable methodology** for any clinical domain where:
- Interpretability is mandatory (psychiatry, oncology, neurology)
- Complex patient narratives require understanding
- Clinical guidelines must be followed explicitly
- Real-time decision support is needed

**The intellectual contribution** is the architecture and its validation principles—applicable to OCD today, depression tomorrow, and general medicine beyond.

---

## 2. STATE OF THE ART

### 2.1 Current Approaches

#### LLM-Only Systems
**Examples:** ChatGPT in medical contexts, general-purpose medical chatbots

**Strengths:**
- Understand nuanced patient language
- Generate contextually appropriate responses
- Require no domain-specific tuning initially

**Failures:**
- Hallucinate medical information (cite nonexistent guidelines)
- Produce inconsistent recommendations (same input → different output)
- Cannot explain reasoning step-by-step
- No formal verification against safety rules
- Risk of patient harm without oversight

**Research:** Hao et al. (2023) showed >30% of LLM medical recommendations violate current guidelines when tested.

#### Knowledge Graph Only
**Examples:** Clinical decision support systems (e.g., IBM Watson for Oncology)

**Strengths:**
- Explicit, auditable reasoning
- Guaranteed guideline compliance (if rules are correct)
- Consistent output
- Clear explanation ("Patient has X → guideline Y applies → action Z")

**Failures:**
- Cannot handle nuance or novel cases
- Requires hand-curation (expensive, slow)
- Brittle when reality deviates from schema
- Cannot learn from new data

**Research:** Modern KG systems struggle with semantic drift and require constant expert maintenance.

#### Hybrid Attempts (Rare)
**Examples:** Few published; most are proprietary/enterprise systems

**Pattern:** Add LLM on top of KG (LLM generates → KG filters). But this is **sequential, not integrated**.

**What's missing:** A principled architecture where:
- LLM reasoning and symbolic reasoning co-design
- Neural networks provide confidence/prediction
- Rules and KG work together, not in sequence

### 2.2 The Gap

**No published work systematically addresses:**
1. How to integrate LLM generations with symbolic rule verification
2. How neural prediction layers (confidence scoring) improve hybrid systems
3. How to formally measure interpretability in clinical AI
4. How such systems perform in real-world clinical workflows (not just labs)

**This is the research contribution.**

---

## 3. PROPOSED ARCHITECTURE

### 3.1 Overview

The **Neuro-Symbolic Clinical Reasoning (NSCR) Architecture** consists of four integrated layers:

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: Neural LLM (Flexible Reasoning)           │
│  • Input: Patient narrative (unstructured text)     │
│  • Process: Parse clinical features, generate       │
│    hypotheses                                        │
│  • Output: Candidate distortion/diagnosis           │
└────────────┬────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────┐
│  LAYER 1.5: Predictive Neural Networks (Confidence) │
│  • Temporal CFI: Predict distortion escalation      │
│  • Rigidity Embedding: Score cognitive rigidity    │
│  • Ensemble: Combine signals → confidence score     │
│  • Output: (prediction, confidence ∈ [0,1])        │
└────────────┬────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────┐
│  LAYER 2: Knowledge Graph (Structured Domain)       │
│  • Input: (Distortion, Confidence)                  │
│  • Process: Query domain knowledge                  │
│    "OCD:contamination_fear → symptoms → ERP         │
│     protocol → contraindications"                   │
│  • Output: Structured candidate recommendations     │
└────────────┬────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────┐
│  LAYER 3: Symbolic Rules (Verification)             │
│  • Input: Recommendation from Layer 2               │
│  • Process: Verify against:                         │
│    - Clinical guidelines (CBT protocol)             │
│    - Safety rules (contraindications)               │
│    - Patient history (allergies, comorbidities)     │
│  • Output: Verified recommendation + explanation    │
└────────────┬────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────┐
│  LAYER 4: Real-World Integration (Obsidian)        │
│  • User interface for clinician/patient             │
│  • Feedback collection (outcome validation)         │
│  • Data for model refinement                        │
└─────────────────────────────────────────────────────┘
```

### 3.2 Layer Specifications

#### **Layer 1: Neural LLM (Flexible Reasoning)**

**Purpose:** Understand unstructured clinical narratives

**Technical Approach:**
- Base model: LLM (Claude, Llama, etc., configurable)
- Task: Extract clinical entities (symptoms, distortions, concerns)
- Output format: Structured JSON
  ```json
  {
    "primary_distortion": "catastrophizing",
    "confidence_llm": 0.78,
    "secondary_distortions": ["all_or_nothing", "emotional_reasoning"],
    "clinical_context": "patient_describes_panic_escalation"
  }
  ```

**Why Layer 1 first:** Only neural models can handle the semantic richness of patient language.

---

#### **Layer 1.5: Predictive Neural Networks (Confidence & Prediction)**

**Purpose:** Score Layer 1 output + predict temporal dynamics

**Three sub-components:**

##### a) Temporal CFI Predictor
- **Input:** Distortion vector from Layer 1 + session history
- **Model:** Causal Transformer (2-3 layers, d_model=32)
- **Output:** Next-turn distortion prediction
- **Question answered:** "Is the patient escalating toward crisis?"
- **Clinical use:** If escalation predicted → increase intervention intensity

##### b) Rigidity Embedding Scorer
- **Input:** Current turn text + distortion from Layer 1
- **Model:** Fine-tuned sentence transformer (MiniLM-L6-v2)
- **Output:** Rigidity score ∈ [0, 1] where 1 = highly rigid
- **Question answered:** "How cognitively rigid is this patient right now?"
- **Clinical use:** Rigidity score modulates technique selection (rigid → more directive)

##### c) Ensemble Confidence
- **Input:** (LLM confidence, Temporal prediction, Rigidity score)
- **Process:** Weighted combination (learnable or fixed)
- **Output:** Final confidence score ∈ [0, 1]
- **Interpretation:** "How sure are we in the Layer 1 diagnosis?"

**Critical property:** This layer surfaces **uncertainty**. If confidence < 0.6:
- Layer 2 KG provides multiple candidate recommendations
- Layer 3 Rules apply extra scrutiny
- Clinician is explicitly flagged

---

#### **Layer 2: Knowledge Graph (Structured Domain)**

**Purpose:** Structure clinical knowledge; guide reasoning

**Domain:** Obsessive-Compulsive Disorder (case study)

**Graph structure (simplified):**
```
OCD
├── Obsessions
│   ├── contamination_fear
│   │   ├── symptoms: [hand_washing, avoidance, ...]
│   │   ├── distortions: [mind_reading, all_or_nothing]
│   │   ├── treatment: [ERP_protocol_A, medication_B]
│   │   └── contraindications: [immersion_if_psychotic, ...]
│   ├── harm_obsession
│   │   ├── symptoms: [checking, reassurance_seeking]
│   │   └── ...
│   └── ...
├── Compulsions
│   └── ...
└── Comorbidities
    ├── depression
    ├── anxiety_disorder
    └── ...
```

**Query interface:**
```
QUERY: "Given contamination_fear + high_rigidity, 
        what is the recommended first-line treatment?"

RESULT: 
{
  "treatment": "Exposure_and_Response_Prevention",
  "intensity": "moderate",  # based on rigidity score
  "first_step": "exposure_to_safe_contaminant",
  "avoid": ["immersion_if_severe_depression"],
  "evidence": "CBT_treatment_guidelines_2023"
}
```

**Implementation:** RDF/OWL or property graph (Neo4j, etc.)

**Maintenance:** Domain experts curate nodes; rules are declarative (changeable without retraining models)

---

#### **Layer 3: Symbolic Rules (Verification)**

**Purpose:** Guarantee safety and guideline compliance

**Rule types:**

##### a) Clinical Guideline Rules
```
Rule: IF recommendation = "exposure_therapy" 
      AND patient_has_active_psychosis = True
      THEN flag = "CONTRAINDICATED"
      AND suggest_alternative = "pharmacotherapy_first"
```

##### b) Safety Rules
```
Rule: IF patient_suicidal_ideation_score > threshold
      AND recommendation_type = "self_reflection"
      THEN escalate_to_clinician = True
      AND recommendation_level = "CRISIS"
```

##### c) Consistency Rules
```
Rule: IF current_recommendation contradicts 
         previous_recommendation_from_3_days_ago
      THEN flag_for_clinician_review = True
      AND explain_reasoning_change
```

**Output:** Recommendation + Explanation chain
```json
{
  "recommendation": "Start ERP with graduated exposure",
  "confidence": 0.89,
  "reasoning": [
    "Step 1 (LLM): Detected contamination fear (0.78)",
    "Step 2 (NN): Escalation predicted; rigidity 0.82",
    "Step 3 (KG): OCD+contamination → ERP protocol",
    "Step 4 (Rules): Checked safety (✓), guidelines (✓), history (✓)",
    "Step 5: APPROVED for delivery"
  ],
  "safety_flags": [],
  "clinician_involvement": "routine review"
}
```

---

#### **Layer 4: Real-World Integration (Obsidian Plugin)**

**Purpose:** Deliver recommendations + collect feedback in clinical workflow

**Workflow:**

```
1. PATIENT WRITES IN OBSIDIAN
   "Today I touched the bathroom door without gloves.
    I feel contaminated and anxious (9/10)."

2. SYSTEM PROCESSES (Layers 1-3)
   [LLM → NN → KG → Rules]

3. OBSIDIAN DISPLAYS RECOMMENDATION
   ┌─────────────────────────────────────────┐
   │ Cognitive Pattern Detected: Catastrophizing
   │ Confidence: 89%
   │ Escalation Risk: Predicted in 3 turns
   │
   │ Recommended Approach:
   │ • Technique: Exposure + Response Prevention
   │ • First Step: Sit with the anxiety for 5 min
   │             without washing
   │ • Rationale: Anxiety naturally decreases over time
   │
   │ ✅ Verified by CBT guidelines
   │ ✅ Safe given your history
   │
   │ [Rate this suggestion: 👍 👎]
   └─────────────────────────────────────────┘

4. PATIENT RESPONDS
   "Tried it. Anxiety went from 9 to 6 in 8 min. Helped."

5. CLINICIAN REVIEWS (end of week)
   Sees: patient response + system recommendation
   Rates: "Good recommendation (8/10 clinical quality)"

6. FEEDBACK LOOP
   • System records: [positive outcome, clinician approved]
   • Updates: NN confidence calibration, KG usage patterns
   • Logs: Data point for research validation
```

**Key property:** Obsidian is not just "UI". It is a **research instrument** that:
- Collects naturalistic patient data (not lab-controlled)
- Integrates clinician feedback
- Enables continuous validation
- Generates longitudinal dataset for analysis

---

### 3.3 Integration Properties

**Neuro-Symbolic means:**

1. **Neural and Symbolic work together, not in sequence**
   - Layer 1 (LLM) generates candidates; Layer 1.5 (NN) scores them
   - Layer 2 (KG) structures; Layer 3 (Rules) verifies
   - Feedback flows backward (Obsidian → Layer 1.5 calibration)

2. **Each layer has a clear job**
   - Don't ask LLM to be interpretable (it can't)
   - Don't ask KG to handle nuance (it can't)
   - Use each where it's strong

3. **Failure modes are explicit**
   - Low confidence → clinician review
   - Rule violation → recommendation rejected
   - Patient outcome negative → system flags

---

## 4. OCD AS CASE STUDY

### 4.1 Why OCD?

OCD is **not** the research focus. **The architecture is.** But OCD is chosen as the validation domain for specific reasons:

#### a) Clear Diagnostic Criteria
- DSM-5 defines OCD precisely (obsessions + compulsions + duration + impairment)
- No ambiguity (unlike "anxiety" or "stress")
- Enables rigorous case selection for pilots

#### b) Standardized Treatment Protocols
- Exposure and Response Prevention (ERP) is evidence-based gold standard
- CBT guidelines are explicit and published
- Layer 3 (Rules) can verify against these directly

#### c) Rich Clinical Narratives
- OCD obsessions are complex, linguistically varied
- Patients describe detailed thought patterns, emotions, compulsions
- Perfect for testing Layer 1 (LLM understanding)

#### d) Abundant Research Literature
- >3000 peer-reviewed papers on OCD + CBT
- Neurobiological mechanisms well-understood
- Comparators and benchmarks exist

#### e) Severe Unmet Need
- 1-2% of population globally (20-40 million people)
- Average 8-17 year delay from symptom onset to diagnosis
- Shortage of trained ERP therapists (especially in LATAM)
- Digital interventions for OCD are rare/generic

### 4.2 OCD Knowledge Graph (Concrete)

Minimum viable graph for this study:

```
NODES (~40 total):

Obsessions
├── contamination_fear (washing, avoidance, hygiene rituals)
├── harm_obsession (fear of harming self/others)
├── sexual_obsession (intrusive sexual thoughts)
├── religious_obsession (blasphemy, sin)
└── symmetry_obsession (order, perfectionism)

Distortions
├── catastrophizing ("If I don't wash, people will die")
├── mind_reading ("They think I'm dirty")
├── all_or_nothing ("Contaminated = completely unsafe")
├── emotional_reasoning ("I feel dirty, so I am dirty")
└── overgeneralization ("Touched one germ, now I'm infected")

Treatment_Protocols
├── ERP_exposure ("Graduated exposure to feared stimulus")
├── ERP_response_prevention ("Resist compulsion for N minutes")
├── cognitive_restructuring ("Challenge the belief")
├── medication ("SSRI as adjunct")
└── acceptance_commitment ("Tolerate discomfort")

Safety_Considerations
├── acute_suicidality ("Do not recommend alone")
├── active_psychosis ("Do not use exposure")
├── severe_depression ("Medication first")
└── compulsion_rituals_extreme ("In-person therapy required")

EDGES (~50 total):

contamination_fear --[symptom]--> hand_washing
contamination_fear --[distortion]--> catastrophizing
contamination_fear --[distortion]--> mind_reading
contamination_fear --[treatment]--> ERP_exposure
ERP_exposure --[contraindication]--> acute_suicidality
hand_washing --[reinforces]--> contamination_fear
...
```

**Size:** Small enough to implement, large enough to be realistic

---

## 5. RESEARCH QUESTIONS

### 5.1 Primary Research Questions

These are the **scientific contributions** that generate publishable papers.

#### **Q1: Interpretability Enhancement**

**Question:** Can a neuro-symbolic architecture produce more interpretable clinical recommendations than an LLM alone?

**Operationalization:**
- **Metric:** Interpretability Fidelity Score (IFS)
  - How well can clinicians explain why the system recommended X?
  - Measured via: clinician reading-comprehension task
- **Measurement:** 30 clinicians rate 50 recommendations
  - LLM-only version (no layers 1.5-3)
  - Full architecture version
  - Rate: "Can you explain in one sentence why this was recommended?"
  - Score: Accuracy of explanation match against designed reasoning chain

- **Dataset:** OCD cases with known ground truth (expert-labeled)
- **Baseline:** LLM-only (Claude/Llama vanilla)
- **Hypothesis:** Full architecture > LLM-only (p < 0.05)

**Success criterion:** IFS(full) - IFS(LLM-only) > 0.25 (25% improvement)

---

#### **Q2: Consistency and Guideline Adherence**

**Question:** Does integrating Knowledge Graphs and symbolic rules reduce inconsistencies and ensure guideline compliance?

**Operationalization:**
- **Metric 1 — Consistency Score (CS):**
  - Same patient, same distortion → does system recommend same treatment?
  - Measured: 20 cases, each presented 3 times (different wording)
  - Score: % of recommendations that match across presentations
  - Baseline (LLM-only): ~60% (high variance)
  - Hypothesis: Full architecture: >95% (rules enforce consistency)

- **Metric 2 — Guideline Compliance (GC):**
  - Does recommendation violate any CBT/OCD guidelines?
  - Measured: Expert checklist (50 safety rules)
  - Score: % of recommendations passing all checks
  - Baseline (LLM-only): ~75% (GPT-4 hallucination rate)
  - Hypothesis: Full architecture: >99% (rules guarantee compliance)

**Dataset:** OCD guidelines from American Psychiatric Association, IOCDF

**Success criterion:** CS > 95% AND GC > 99%

---

#### **Q3: Neural Prediction Calibration**

**Question:** Do Layers 1.5 (Temporal CFI + Rigidity Embedding) improve confidence scoring and escalation detection?

**Operationalization:**
- **Metric 1 — Confidence Calibration:**
  - System predicts confidence ∈ [0,1]
  - Ground truth: Clinician rates recommendation as Good/Poor
  - Expected Calibration Error (ECE): |predicted_confidence - actual_accuracy|
  - Baseline (no NN layer): ECE = 0.18
  - Hypothesis: With NN layer: ECE < 0.10 (better calibration)

- **Metric 2 — Escalation Detection:**
  - System predicts: "Will this patient's CFI worsen in next 3 turns?"
  - Ground truth: Does it actually worsen?
  - Measured: AUROC of prediction
  - Baseline (persistence model): AUROC = 0.62
  - Hypothesis: Temporal CFI NN: AUROC > 0.75

**Dataset:** 50 OCD patient journeys, 7+ turns each

**Success criterion:** ECE < 0.10 AND AUROC > 0.75

---

#### **Q4: Knowledge Graph Completeness**

**Question:** What representation of clinical knowledge (graph structure, node/edge types) best facilitates accurate therapeutic reasoning?

**Operationalization:**
- **Alternative representations tested:**
  - A) Simple property graph (current design)
  - B) RDF/OWL ontology (more formal)
  - C) Lightweight schema (fewer nodes/edges, faster queries)

- **Metric:** Clinical accuracy
  - Expert clinicians rate: "For this case, does the KG produce sound recommendations?"
  - 30 cases × 3 KG versions = 90 evaluations
  - Score: % clinician approval

- **Hypothesis:** Properties graphs (A) ≥ RDF (B) in usability; both > simplified (C)

**Dataset:** OCD expert consensus on graph structure

**Success criterion:** Selected representation: >85% clinician approval

---

#### **Q5: Real-World Performance (Obsidian Integration)**

**Question:** Does the architecture maintain accuracy and interpretability in a real clinical workflow (not lab-controlled)?

**Operationalization:**
- **Pilot study:** 8-10 OCD patients, 6-8 weeks, Obsidian plugin
- **Metrics:**
  - Recommendation adoption rate: Do patients follow suggestions?
  - Outcome correlation: Does following recommendations → CFI improvement?
  - Clinician satisfaction: Does clinician approve recommendations?
  - System calibration: Do NN confidence scores match actual quality?

- **Measurement:**
  - Each recommendation: patient response + clinician review
  - Weekly: aggregate metrics
  - End: clinician interview on usability

- **Baseline:** Traditional CBT (therapist-delivered)
- **Hypothesis:** Digital recommendations correlate with outcome (r > 0.6)

**Dataset:** Real patients from partner clinic

**Success criterion:** Adoption rate >70% AND clinician satisfaction >8/10

---

### 5.2 Secondary Research Questions

#### **Q1b: Tradeoffs Between Interpretability and Flexibility**

**Question:** As we add symbolic constraints (rules, KG), does recommendation flexibility decrease? Where is the optimal tradeoff?

**Hypothesis:** High interpretability (many rules) → rigid responses to novel cases. Trade-off is real.

**Measurement:** 
- Present 20 "atypical OCD cases" (not in typical presentation)
- Full architecture vs. LLM-only
- Score: Can system handle novelty while maintaining interpretability?

**Paper angle:** "The Interpretability-Flexibility Tradeoff in Clinical AI"

---

#### **Q6: Failure Mode Analysis**

**Question:** When and why does the architecture fail?

**Measurement:**
- Run across 100 diverse OCD cases
- Classify failures: LLM layer (wrong distortion), NN layer (wrong confidence), KG layer (missing protocol), Rules layer (over-strict)
- Document each failure with root cause

**Paper angle:** "When Neuro-Symbolic Reasoning Fails: Edge Cases in Clinical OCD Treatment"

---

## 6. METHODOLOGY

### 6.1 Research Design

**Type:** Mixed-methods design combining:
1. Computational validation (Q1-Q4 quant metrics)
2. Clinical validation (Q5 pilot + clinician feedback)
3. Qualitative analysis (failure modes, design recommendations)

### 6.2 Evaluation Framework

| Question | Metric | Dataset | Baseline | Success Criterion |
|----------|--------|---------|----------|-------------------|
| Q1 | IFS (Interpretability Fidelity) | 50 cases | LLM-only | IFS diff > 0.25 |
| Q2a | CS (Consistency Score) | 20 cases × 3 | ~60% | >95% |
| Q2b | GC (Guideline Compliance) | 100 rules × cases | ~75% | >99% |
| Q3a | ECE (Calibration Error) | 50 cases | 0.18 | <0.10 |
| Q3b | AUROC (Escalation prediction) | 50 cases, 7+ turns | 0.62 | >0.75 |
| Q4 | Clinician approval (KG design) | 30 cases | N/A | >85% |
| Q5 | Real-world metrics | 8-10 patients, 6-8 weeks | Therapist-delivered | Adoption >70%, satisfaction >8/10 |

### 6.3 Data Sources

1. **Synthetic OCD cases:** For early validation (Q1-Q4)
   - Generated from clinical literature + expert consensus
   - Covers the diagnostic spectrum (contamination → harm → sexual → religious → symmetry)

2. **Structured expert feedback:** For Q1, Q2a, Q4
   - Recruit 10-15 licensed CBT clinicians
   - 30-min structured interviews per clinician

3. **Real patient data:** For Q5 (Obsidian pilot)
   - Partner with 1-2 mental health clinics
   - 8-10 OCD patients, informed consent
   - Ethical approval required (IRB)

4. **Published OCD guidelines:**
   - DSM-5 Diagnostic Criteria
   - American Psychiatric Association CBT Guidelines
   - IOCDF Treatment Recommendations
   - PubMed literature review (2020-2025)

### 6.4 Validation Protocol

**Stage 1: Bench Validation (Months 1-3)**
- Implement Layers 1-3 (LLM, NN, KG, Rules)
- Test Q1-Q4 using synthetic OCD cases
- Iterate based on results

**Stage 2: Clinical Validation (Months 4-6)**
- Implement Layer 4 (Obsidian integration)
- Recruit pilot patients
- Collect real-world data
- Test Q5

**Stage 3: Analysis & Iteration (Months 7-9)**
- Analyze results across all questions
- Identify failure modes (Q6)
- Refine architecture based on findings
- Write papers

---

## 7. REAL-WORLD INTEGRATION: OBSIDIAN PLUGIN

### 7.1 Obsidian as Research Instrument

Obsidian is not just a "nice interface." It serves three critical functions:

#### 1. Naturalistic Data Collection
- Patient writes about OCD in their own words, not prompted
- No lab setting, no artificial structure
- Captures temporal dynamics (daily entries)
- Rich context (comorbidities, life events)

#### 2. Clinician Feedback Loop
- Therapist reviews Obsidian notes + system recommendations
- Ratings: "How clinically sound was this recommendation?" (1-10)
- Qualitative: "What could improve?"
- This feedback trains the model (calibration, future iterations)

#### 3. Outcome Measurement
- Patient rates: "Did this help?" (1-10)
- System tracks: CFI trajectory over time
- Correlation: Recommendation quality ↔ Patient improvement

### 7.2 Data Flow

```
PATIENT
  │
  ├→ Writes in Obsidian (narrative)
  │
  └→ System processes (Layers 1-3)
      │
      ├→ Extracts: distortion, confidence, prediction
      ├→ Queries: KG for protocol
      ├→ Verifies: Rules for safety
      │
      └→ Generates: Recommendation + explanation
          │
          ├→ Display in Obsidian
          │
          ├→ Patient rates: helpful? (1-10) + free text
          │
          └→ Clinician reviews weekly
              │
              ├→ Clinician rate: "clinically sound?" (1-10)
              │
              └→ System logs:
                  outcome (helpful/not)
                  clinician feedback
                  → updates confidence calibration
                  → data for research validation
```

### 7.3 Privacy & Ethics

- **Local-first:** Obsidian data stored locally, not sent to cloud
- **Consent:** Patients explicitly consent to research use
- **Anonymization:** All data de-identified before analysis
- **IRB approval:** Required before recruiting real patients

---

## 8. EXPECTED RESEARCH OUTPUTS

### 8.1 Publications

**Paper 1 (Core contribution):**
- **Title:** "Neuro-Symbolic Reasoning for Clinical Decision Support: Design and Validation of an OCD Treatment Recommendation System"
- **Venue:** ACM Transactions on Computing for Healthcare / Nature Digital Medicine
- **Scope:** Architecture design (Layers 1-3), Q1-Q4 results
- **Authors:** You + domain experts (psychiatrist, NLP researcher, KG expert)

**Paper 2 (Real-world validation):**
- **Title:** "Clinical Validation of Neuro-Symbolic Recommendations in Obsessive-Compulsive Disorder: An Obsidian Plugin Pilot Study"
- **Venue:** Journal of Obsessive-Compulsive and Related Disorders
- **Scope:** Q5 (Obsidian pilot), outcome correlation, clinician feedback
- **Authors:** You + clinician partner + patients

**Paper 3 (Neural prediction):**
- **Title:** "Temporal Dynamics and Rigidity Scoring in OCD: Integrating Neural Networks with Symbolic Clinical Reasoning"
- **Venue:** IEEE Journal of Biomedical and Health Informatics
- **Scope:** Layer 1.5 (NN contribution), Q3 results, confidence calibration

**Paper 4 (Failure analysis):**
- **Title:** "When Neuro-Symbolic Reasoning Fails: Edge Cases and Limitations in Clinical OCD Treatment"
- **Venue:** ACM FAccT (Fairness, Accountability, Transparency)
- **Scope:** Q6, failure modes, design recommendations

### 8.2 Software Artifacts

1. **Nausica Core** (GitHub, open-source)
   - Layers 1-3 implemented (Python/FastAPI)
   - Modular design (replace LLM, KG, rules easily)
   - Documentation for researchers

2. **Obsidian Plugin** (GitHub, npm package)
   - Real-time integration with Nausica Core
   - Privacy-first (local-first architecture)
   - Clinical feedback UI
   - Published on Obsidian plugin marketplace

3. **OCD Knowledge Graph** (GitHub, RDF/N-Triples)
   - Curated graph of OCD concepts
   - Reusable for other researchers
   - Version-controlled updates

4. **Benchmark Dataset**
   - 100 synthetic OCD cases (curated)
   - Labels: ground-truth distortion, recommended treatment
   - Splits: train/val/test for reproducibility
   - Published on Zenodo

### 8.3 Thesis Structure

**Chapter 1:** Introduction + State of Art (this proposal)

**Chapter 2:** Neuro-Symbolic Architecture Design
- Layers 1-3 technical details
- Design decisions and rationale
- OCD instantiation

**Chapter 3:** Computational Validation
- Q1-Q4 experiments
- Bench results
- Analysis and interpretation

**Chapter 4:** Clinical Validation
- Q5 (Obsidian pilot)
- Real-world data, clinician feedback
- Outcome correlations

**Chapter 5:** Failure Analysis & Limitations
- Q6 and secondary questions
- When the architecture breaks
- Generalizability to other domains

**Chapter 6:** Conclusion & Future Work
- Summary of contributions
- Roadmap for extension (depression, panic, etc.)
- Policy/clinical practice implications

---

## 9. TIMELINE & ROADMAP

### Year 1: Foundation (Months 1-12)

| Phase | Months | Tasks | Deliverable |
|-------|--------|-------|-------------|
| Design | 1-2 | Formalize architecture; literature review | Arch. spec document |
| Implementation | 3-5 | Code Layers 1-3; build OCD KG | Prototype |
| Bench Validation | 6-7 | Test Q1-Q4; synthetic cases | Results + Paper 1 draft |
| Clinician Review | 8-9 | Recruit clinicians; gather feedback | Refinements |
| Write-up | 10-12 | Complete Paper 1; thesis Ch 1-3 | Paper 1 submitted |

**Year 1 Output:** Paper 1 (core contribution), refined architecture, ready for real-world validation

---

### Year 2: Clinical Integration (Months 13-24)

| Phase | Months | Tasks | Deliverable |
|-------|--------|-------|-------------|
| Obsidian Dev | 13-15 | Implement Layer 4; privacy setup | Plugin beta |
| Pilot Recruitment | 16 | IRB approval; recruit 8-10 patients | Pilot cohort |
| Pilot Study | 17-21 | 6-8 weeks with patients; clinician feedback | Real-world data |
| Analysis | 22-23 | Analyze Q5; failure modes (Q6) | Papers 2+3 drafts |
| Write-up | 24 | Complete Papers 2-3; thesis Ch 4-5 | Papers 2-3 submitted |

**Year 2 Output:** Papers 2-3 (clinical validation), software released, thesis draft complete

---

### Year 3-4: Generalization & Defense

| Phase | Months | Tasks | Deliverable |
|-------|--------|-------|-------------|
| Extension | 25-30 | Extend to depression; validate generalizability | Paper 4 draft |
| Refinement | 31-40 | Address reviewer feedback; polish publications | Papers 1-4 published |
| Thesis | 41-44 | Final revision of all chapters; defense prep | Thesis defense |

**Year 3-4 Output:** 4 papers published, software mature, thesis defended

---

## 10. TRANSFERABILITY & FUTURE WORK

### 10.1 Generalization Beyond OCD

The architecture (Layers 1-3) is **domain-agnostic**. To apply to another disorder:

**Required changes:**
- Layer 2 (KG): Swap OCD subgraph for depression/panic subgraph
- Layer 3 (Rules): Update clinical guidelines
- Dataset (Q5): New patient pilot

**Minimal changes:**
- Layer 1 (LLM): Same model, just different prompts
- Layer 1.5 (NN): Retrainable on new data

**Timeline:** Extending to 2 additional disorders = 1 additional year per disorder

### 10.2 Future Roadmap (Beyond Thesis)

**Postdoc / Industry Applications:**
- **Year 5:** Extend to depression, anxiety disorder (2+ additional papers)
- **Year 6:** Integrate with EHR systems (clinical deployment)
- **Year 7:** Multi-language support, cross-cultural variants

**Research Directions:**
- RL from clinician feedback (DPO fine-tuning)
- Temporal reasoning (predict CFI trajectory weeks ahead)
- Multimodal integration (speech, facial expression)
- Personalization (adapt recommendations per patient learning curve)

---

## 11. BUDGET CONSIDERATIONS (Not Detailed Here)

This proposal is designed to be **achievable with modest resources:**

- **Computing:** GPU access (Google Colab free tier, or modest AWS budget)
- **Software:** Open-source stack (Python, FastAPI, Neo4j, Obsidian SDK)
- **Clinical partnership:** In-kind (partner clinic, volunteer clinicians)
- **Data:** Synthetic OCD data (generated, not purchased)

---

## 12. REFERENCES

### Foundational Work
- Hao et al. (2023). "Evaluating and Improving Large Language Models for Clinical Decision Support." *Nature Medicine*.
- Rudin, C. (2019). "Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and Use Interpretable Models Instead." *Nature Machine Intelligence*.

### OCD & CBT
- American Psychiatric Association. (2013). *Diagnostic and Statistical Manual of Mental Disorders (5th ed.)*.
- Foa, E. B., Liebowitz, M. R., et al. (2005). "Randomized, Placebo-Controlled Trial of Exposure and Ritual Prevention, Clomipramine, and Their Combination in the Treatment of OCD." *American Journal of Psychiatry*.

### Neuro-Symbolic AI
- Garnelo, M., & Shanahan, M. (2019). "Reconciling Deep Learning and Symbolic AI: Representing Logic Structures Ontologically." *Journal of Logic, Language and Information*.
- Mao, J., Gan, C., et al. (2019). "The Neuro-Symbolic Visual Question Answering Challenge." *ICCV Workshop*.

### Knowledge Graphs in Healthcare
- Hristoskova, A., et al. (2021). "Knowledge Graphs in Healthcare." *IEEE Access*.
- Rotmensch, M., Halpern, Y., et al. (2017). "Learning a Health Knowledge Graph from Electronic Medical Records." *Scientific Reports*.

---

## APPENDIX: Architecture Diagram (Text)

```
PATIENT JOURNEY: OCD Contamination Fear

INPUT:
"Today I touched the bathroom door handle without gloves.
 Now I feel completely contaminated. My hands feel dirty.
 I've washed them 5 times but it doesn't feel clean."

LAYER 1 (LLM):
├─ Distortion detected: contamination_fear
├─ Secondary: all_or_nothing ("completely contaminated")
├─ Emotional signal: anxiety, urgency
└─ Confidence (LLM): 0.78

LAYER 1.5 (Neural Networks):
├─ Temporal CFI: Predicts escalation (9→8→7 next 3 turns)
│  └─ Confidence: 0.71
├─ Rigidity Embedding: Current rigidity = 0.82 (high)
├─ Ensemble confidence: mean([0.78, 0.71, 0.82]) = 0.77
└─ Decision: "Proceed with confidence 0.77, flag for clinical review"

LAYER 2 (Knowledge Graph):
└─ Query: contamination_fear + high_rigidity
   └─ Path: OCD → contamination → symptoms → treatment
      └─ Recommended: ERP_exposure
      └─ Intensity: MODERATE (based on rigidity 0.82)
      └─ First step: "Sit with anxiety for 5 min without washing"
      └─ Rationale: "Anxiety naturally decreases (habituation)"

LAYER 3 (Symbolic Rules):
├─ Check: "Is patient suicidal?" → No ✓
├─ Check: "Is patient psychotic?" → No ✓
├─ Check: "Does ERP violate guidelines?" → No ✓
├─ Check: "Contraindication?" → None ✓
├─ Consistency check: "Is this consistent with yesterday?" → Yes ✓
└─ APPROVAL: Recommendation verified

LAYER 4 (Obsidian Display):
┌───────────────────────────────────────┐
│ NAUSICA Clinical Assistant            │
├───────────────────────────────────────┤
│ Pattern: Contamination fear detected  │
│ Confidence: 77%                       │
│                                       │
│ Your anxiety is escalating.           │
│ Recommended: Exposure practice        │
│                                       │
│ Try this:                             │
│ Sit with the contaminated feeling     │
│ for 5 minutes WITHOUT washing.        │
│                                       │
│ Your anxiety will peak, then drop.    │
│ This is normal—brain is learning.     │
│                                       │
│ [How helpful? 👎 😐 👍 👍👍]        │
│                                       │
│ (Note: Your therapist reviews this)  │
└───────────────────────────────────────┘

PATIENT RESPONSE:
"Tried it. Anxiety went 9 → 6 in 8 minutes. Worked!"

CLINICIAN REVIEW (end of week):
Rating: "Clinical quality 8/10, sound reasoning"

SYSTEM FEEDBACK LOOP:
├─ Outcome: POSITIVE (CFI improved)
├─ Clinician approval: YES
├─ Update NN confidence: +0.05 (from 0.77 → 0.82)
└─ Record for Q5 validation
```

---

## CLOSING STATEMENT

This research addresses a fundamental challenge in clinical AI: **How do we build systems that are both flexible (understanding patient nuance) and interpretable (clinically defensible)?**

The neuro-symbolic approach is not a band-aid. It is a principled methodology that:
1. Combines the strengths of neural and symbolic reasoning
2. Makes clinical reasoning explicit and auditable
3. Scales beyond the initial domain (OCD → depression → medicine)
4. Generates publications across ML, healthcare, and clinical venues

The work is feasible, well-scoped, and designed to produce a doctoral thesis of strong academic rigor and real-world impact.

---

**Document prepared by:** [Your Name]  
**Date:** July 8, 2026  
**Version:** 1.0 (Proposal)

