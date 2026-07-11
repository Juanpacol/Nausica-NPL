# Análisis de Nichos — Nausica

## Context from Deep Research (Fase 1)

**Beck vs Ellis:**
- Beck (CT): Empirical, "evidence first" approach. Validation through thought records. Pioneered depression treatment.
- Ellis (REBT): Philosophical, "dispute first" approach. Direct challenge of irrational beliefs. 4 core irrationals: demandingness, awfulizing, low frustration tolerance, global self-rating.

**CBT Efficacy (current state):**
- Depression subclinical: moderate effect (g=-0.56)
- Anxiety in neurological disorders: small effect (g=0.38)
- **Gap**: Small effect sizes suggest room for mechanistic improvement via real-time intervention.

---

## Potential Nichos for Nausica

### **1. PANIC DISORDER (Pánico)**

**Why this niche?**
- **Core distortion**: CATASTROPHIZING (Ellis would say: "awfulizing")
- **Mechanism**: Single catastrophic thought → physical symptoms (racing heart) → misinterpretation of symptoms as sign of dying/heart attack → more panic
- **Current gap**: Most apps do static psychoeducation ("panic attacks aren't dangerous") but don't DETECT the catastrophic thought in real-time

**Where Nausica wins:**
- Detects catastrophizing BEFORE panic spiral
- Formalizes Socratic reframing (technique: Downward Arrow from Beck)
- Temporal transformer could predict if client is escalating → early intervention
- CFI (Cognitive Flexibility Index) directly measures panic proneness

**Research hooks:**
- Early detection prevents escalation (cite: baseline severity moderates CBT efficacy)
- Real-time cognitive restructuring > post-hoc coping skills
- Beck specializes in panic disorder → existing literature base

**Estimated addressable:**
- Global panic disorder prevalence: 2-3% of population
- Limited access to trained therapists (gap in LATAM)
- High relapse rate without maintenance (maintenance tool angle)

---

### **2. OCD (Obsessive-Compulsive Disorder)**

**Why this niche?**
- **Core distortions**: mind-reading ("If I think it, it means I want it"), all-or-nothing ("contaminated = completely unsafe"), perfectionism variants
- **Mechanism**: Intrusive thought → over-interpretation ("What if this means I'm a bad person?") → compulsion → temporary relief → escalation
- **Current gap**: OCD requires MONITORING compulsion urges (when do they spike?) + MAPPING distortions to compulsion triggers

**Where Nausica wins:**
- Detect mind-reading distortions specific to OCD fears
- Temporal tracking: "Is the CFI improving when we use this technique vs that one?"
- Integration with exposure therapy (track which exposures correspond to distortion reduction)
- Fable policy can distinguish OCD-specific techniques (e.g., acceptance/tolerance vs. Beck's evidence-exam)

**Research hooks:**
- OCD is undertreated in digital health (most apps are generic anxiety)
- Real-time tracking of compulsion urges + distortions (novel data source)
- CFI as a continuous measure of OCD severity (vs binary questionnaires)

**Estimated addressable:**
- Global OCD prevalence: 1-2% of population
- Extremely underdiagnosed in LATAM (stigma)
- Currently 8-17 years from symptom onset to treatment (detection early = major impact)

---

### **3. DEPRESSION (Maintenance / Residual)**

**Why this niche?**
- **Core distortions**: All-or-nothing, overgeneralization, emotional reasoning
- **Mechanism**: Depressive episode → some treatment → partial remission → residual symptoms + rumination → relapse
- **Current gap**: Maintenance tools don't target EARLY rumination detection; focus is on crisis intervention

**Where Nausica wins:**
- Early detection of rumination (overgeneralization pattern)
- Continuous CFI tracking signals relapse risk BEFORE crisis
- Integration with journaling (Obsidian plugin = natural daily use case)
- Beck's original domain (extensive literature)

**Research hooks:**
- Depression residual symptoms are common (30-40% of treated patients)
- CBT as maintenance (not just acute) is under-studied in digital context
- CFI as relapse predictor (novel use)

**Estimated addressable:**
- Global depression prevalence: 5% of population
- Relapse within 2 years post-treatment: ~50%
- Maintenance tool market = recurring revenue (vs. one-time therapy)

---

## Recommendation: Pick 1 for MVP, Stack Others

### **Option A: Go deep on PANIC (Highest impact + clearest mechanism)**
- Rationale: Panic has sharpest distortion-mechanism link (catastrophizing → panic cycle is tight)
- Research: Beck's panic protocol is well-documented
- Differentiation: Real-time catastrophizing detection + temporal prediction
- Pilot: 10 patients with panic disorder, 5-session arc, measure CFI + panic rating correlation
- Paper angle: "Early Detection of Catastrophic Thinking Prevents Panic Escalation: A Temporal CBT Study"

### **Option B: Go deep on OCD (Highest unmet need + rarest intervention)**
- Rationale: OCD severely underserved in digital health; long pathway to diagnosis
- Research: Less literature than panic, but mind-reading + all-or-nothing are OCD-specific
- Differentiation: Compulsion-tracking + distortion correlation (novel measurement)
- Pilot: 5-8 patients with OCD, track compulsion urges vs. CFI scores
- Paper angle: "Real-Time Cognitive Distortion Mapping in OCD: A Digital Monitoring Framework"

### **Option C: Go broad but POSITION as "depression maintenance" (Safest, recurring revenue)**
- Rationale: Depression maintenance is underserved but less research-novel
- Differentiation: Continuous relapse prediction via CFI + rumination detection
- Pilot: Post-treatment depression cohort (easier to recruit)
- Paper angle: "Relapse Prevention via Continuous Cognitive Flexibility Monitoring"

---

## Next Steps (Pending Phase 2 Research)

1. Validate prevalence + digital health gap for each niche
2. Confirm distortion-mechanism specificity
3. Find 1-2 published protocols we can benchmark against
4. Decide on MVP niche based on:
   - Research novelty (what will get published?)
   - Pilot feasibility (can we recruit + retain users?)
   - Revenue model (one-time therapy vs. maintenance subscription?)

---

## Files to Update After Decision

- `CLAUDE.md`: refine project scope to chosen niche
- `docs/VALIDATION.md`: add niche-specific benchmark metrics
- `docs/CFI_SPECIFICATION.md`: validate CFI relevance to chosen disorder
- `README.md`: elevator pitch for investors/reviewers

