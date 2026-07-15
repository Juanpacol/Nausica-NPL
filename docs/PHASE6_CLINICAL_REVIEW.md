# Phase 6 — Clinical Review Packet (OCD Knowledge Graph)

**For:** the OCD/ERP clinical psychologist reviewing this project's Layer 2
(Knowledge Graph) content.

**Status of the content you're reviewing:** `configs/knowledge_graph/ocd_nodes.yaml`
and `ocd_edges.yaml` are an **AI-assisted draft**, synthesized from the
peer-reviewed literature already gathered for this project (citations are
inline in the YAML files, per node/edge). **Nothing in these files has been
clinically validated.** Your review has full veto power — add, remove, or
rewrite anything. Nothing here is used in a real patient-facing
recommendation until you sign off.

---

## 1. What you're being asked to do

1. Read through `ocd_nodes.yaml` (47 nodes) and `ocd_edges.yaml` (62 edges).
   Both files were self-checked programmatically before this handoff for
   referential integrity (every edge points to a real node) and reachability
   (every obsession connects through to at least one protocol) — so what
   you're reviewing is internally consistent, even though it is not yet
   clinically validated.
2. For each item flagged `review_flag: "EXPERT..."` in the YAML, make an
   explicit decision: keep, edit, or delete.
3. For everything *not* explicitly flagged, still review it — the flags mark
   what the drafting process considered highest-risk or lowest-confidence,
   not an exhaustive list of what needs scrutiny.
4. Look for **missing** content, not just errors in what's there — especially
   missing contraindications (see §4 below), which is the single most
   safety-critical gap category.
5. Fill in the sign-off table at the end of this document.

You do not need to touch any Python code. Everything you're reviewing is
plain-text YAML.

---

## 2. Why this structure (KG vs. Rules split)

Two things live in separate places, on purpose:

- **`ocd_nodes.yaml` / `ocd_edges.yaml` (what you're reviewing now):**
  declarative facts only — "contamination fear is treated with graduated
  exposure." No conditional logic.
- **`configs/rules.yaml` (separate document, not in this packet):**
  procedural logic — "if confidence is low, force clinician review." This
  will need your review too, but it's a distinct sign-off (Phase 8).

This split means a change to "what protocol treats X" never silently changes
"when do we escalate to a human," and vice versa.

---

## 3. Node-by-node review checklist

For each `NodeType`, here is what to check:

| NodeType | What to verify |
|---|---|
| `obsession` | Is this a real, distinct clinical category? Should any be split further or merged (e.g., should sexual/religious merge into one "forbidden thoughts" node, per the 4-factor OCD model)? Is the DSM-5 code field accurate (note: DSM-5/ICD-10-CM does not code content-subtypes separately — see the caveat at the top of `ocd_nodes.yaml`)? |
| `symptom` | Does this symptom genuinely, specifically follow from its parent obsession (not a generic anxiety behavior)? Are there major compulsion types missing for that obsession? |
| `distortion` | Does the `taxonomy_label` correctly match one of the 5 types the classifier already uses (`all_or_nothing`, `overgeneralization`, `emotional_reasoning`, `catastrophizing`, `mind_reading` — see `docs/TAXONOMY.md`)? (This is enforced by an automated check; don't introduce new labels here.) |
| `cbt_technique` | Is this a real, named technique in the ERP/CBT literature? Is anything missing (e.g., D-cycloserine augmentation, family-based ERP for pediatric cases)? |
| `erp_protocol` | Does `first_line: true/false` match your clinical judgment and the Katzman et al. (2014) Canadian guideline this project has adopted as its primary reference? |
| `contraindication` | **Highest priority.** Is the `reason` clinically accurate and complete? Is anything **missing** (see §4)? |
| `patient_state` | Are the `threshold` values (e.g., `suicidal_risk: 0.7`) clinically defensible, or arbitrary placeholders that need replacing with a real instrument (e.g., C-SSRS for suicidality, BABS for insight)? |

---

## 4. Contraindications — please actively look for gaps

The current draft has 6 contraindication nodes:

1. Active psychosis
2. Severe/imminent suicidality
3. Untreated severe major depressive episode
4. Active, unmanaged substance use disorder
5. Poor/absent insight
6. Medical instability from compulsions

**This list is very likely incomplete.** Candidates you may want to add
(not pre-populated, because guessing at safety-critical content without your
input is worse than leaving it blank):

- Pregnancy-specific considerations for certain pharmacological augmentations
- Pediatric-specific contraindications, if the system will ever be used with
  minors
- Specific comorbid conditions (e.g., certain personality disorder
  presentations, dissociative symptoms during exposure)
- Cultural/religious considerations for the scrupulosity protocol
  specifically (flagged in `erp_protocol_religious_graduated`)

Please treat this section as a starting checklist, not a ceiling.

---

## 4b. A structural note (not clinical — you can skip the "why," just know the "what")

Every safety-critical `contraindication_*` node (e.g. `contraindication_active_psychosis`)
has a matching `patient_state_*` node (e.g. `patient_state_active_psychosis`), linked via
a `contraindication_ref` field. This is a code-architecture detail: the graph's edge rules
require the actual blocking edge to originate from the `patient_state_*` node, while the
`contraindication_*` node holds the human-readable `reason` text. **You do not need to
review this twice** — reviewing the `reason` text on the `contraindication_*` node and the
`threshold`/definition on its linked `patient_state_*` node covers both.

## 5. Edge-by-edge review checklist

| EdgeType | What to verify |
|---|---|
| `triggers` (obsession → symptom) | Does this obsession really trigger this specific symptom, at roughly this strength? |
| `manifests_as` (symptom → distortion) | **Lowest-confidence section in this draft** — assigning a *single* dominant distortion to a compulsion is a clinical judgment call, not something the literature mining could verify directly. Expect to rewrite most of these. |
| `addressed_by` (distortion → technique) | Does this technique genuinely target this distortion, or is it more general-purpose? |
| `steps_in` (technique → protocol) | Does this technique actually belong in this protocol, in this combination? |
| `contraindicates` (contraindication → protocol) | **Safety-critical.** Is the `action` (`escalate` vs. `flag`) proportionate? Is any protocol missing a contraindication edge it should have? |
| `escalates_to` (patient_state → patient_state) | These are the weakest-evidence edges in the draft (project hypotheses about risk trajectories, not established clinical fact — see the `review_flag` notes referencing Feusner et al. 2015's caution about self-report/language-derived signals underperforming for OCD relapse prediction). Scrutinize these hardest. |

Every edge also carries a `strength` value (0–1). These are **all AI-estimated
placeholders** — please don't spot-check a few and assume the rest are fine;
assign your own values throughout.

---

## 6. What happens after your review

1. You send back edits (in the YAML directly, in a copy, or as a list of
   changes — whatever's easiest for you).
2. Changes get merged into `ocd_nodes.yaml` / `ocd_edges.yaml`.
3. Separately (not part of this packet), you'll be asked to produce an
   **independent checklist** of "obsession + distortion + patient state →
   correct protocol" test cases, created *without* looking at the KG content
   you just reviewed. This is used later to test whether the system's
   recommendations match your clinical judgment (Research Question Q2) —
   keeping it independent avoids the checklist just checking the KG against
   itself.
4. Only after both are signed off does this content get used in any
   patient-facing (or even bench-test) recommendation path.

---

## 7. Sign-off

| Item | Status | Reviewer | Date | Notes |
|---|---|---|---|---|
| `ocd_nodes.yaml` — obsessions (5) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — symptoms (10) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — distortions (5) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — techniques (7) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — protocols (6) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — contraindications (6 + additions) | ☐ Approved ☐ Needs changes | | | |
| `ocd_nodes.yaml` — patient states (8) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — triggers (10) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — manifests_as (10) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — addressed_by (11) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — steps_in (13) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — contraindicates (14 + additions) | ☐ Approved ☐ Needs changes | | | |
| `ocd_edges.yaml` — escalates_to (4) | ☐ Approved ☐ Needs changes | | | |
| **Overall Phase 6 sign-off** | ☐ Signed off | | | |

