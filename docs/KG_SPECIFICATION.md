# OCD Knowledge Graph — Specification (Skeleton)

> **Status:** outline only — Phase 6 (expert curation) and Phase 9
> (`OCDGraph` implementation) are not started. This document is the
> placeholder structure to fill in as those phases land; see
> `docs/IMPLEMENTATION_PLAN.md` §3 (Layer 2) and §4 (Phases 6, 9) for the
> authoritative scope and timeline.

Implementation: `src/knowledge_graph/` (`schema.py`, `ocd_graph.py`).
Content: `configs/knowledge_graph.yaml`,
`configs/knowledge_graph/ocd_nodes.yaml`, `ocd_edges.yaml`. Tests: deferred
to Phase 9.

## 1. Purpose & design rationale

- *(fill in Phase 9)* Why a knowledge graph at all — declarative domain
  facts, separate from the procedural inference in `src/rules_engine/`
  (Layer 3). Restate the KG/Rules invariant from
  `docs/IMPLEMENTATION_PLAN.md` §3: Layer 2 answers "what is true in the
  domain," Layer 3 answers "what follows for this patient."
- *(fill in Phase 9)* Why `networkx` over Neo4j/RDF at this scale (~40
  nodes, ~50 edges) — see "Stack decisions" table in
  `docs/IMPLEMENTATION_PLAN.md` §3.

## 2. Node types & metadata

- *(fill in Phase 6/9)* One subsection per `NodeType`
  (`src/knowledge_graph/schema.py`): OBSESSION, SYMPTOM, DISTORTION,
  CBT_TECHNIQUE, ERP_PROTOCOL, CONTRAINDICATION, PATIENT_STATE.
- *(fill in Phase 6/9)* Required vs optional `metadata` fields per type
  (e.g. `dsm5_code`, `severity_scale` for OBSESSION), with the canonical
  example row from `configs/knowledge_graph/ocd_nodes.yaml`.

## 3. Edge types & semantics

- *(fill in Phase 6/9)* One subsection per `EdgeType`: TRIGGERS,
  MANIFESTS_AS, ADDRESSED_BY, STEPS_IN, CONTRAINDICATES, ESCALATES_TO —
  which node-type pairs each connects, and what `strength` means for that
  edge type.

## 4. Query interfaces

- *(fill in Phase 9)* `query_treatment(obsession, distortion, rigidity)` —
  algorithm (graph traversal from obsession to protocol), return shape,
  and how `rigidity` affects `severity_recommendation` without affecting
  which protocol is selected (F2 invariant — rigidity modulates delivery,
  never confidence; see `docs/IMPLEMENTATION_PLAN.md` §3, Layer 1.5).
- *(fill in Phase 9)* `explain_path(start_node, end_node)` — shortest-path
  semantics, tie-breaking, and how the output feeds
  `VerifiedRecommendation.reasoning_chain` (`src/rules_engine/verification.py`).

## 5. Extension points (generalization beyond OCD)

- *(fill in Phase 9+)* How a future depression/panic subgraph would swap
  in: same `NodeType`/`EdgeType` vocabulary, different
  `configs/knowledge_graph/*.yaml` content, zero code changes to
  `OCDGraph` (module may need renaming at that point — tracked as future
  work, not Year-1 scope per `docs/IMPLEMENTATION_PLAN.md` §2 "Scope /
  No-scope").

## 6. Known limitations (disclose always)

- *(fill in Phase 6/9)* Hand-curated content, no automatic KG construction
  (explicitly out of scope for Year 1 — `docs/IMPLEMENTATION_PLAN.md` §2).
- *(fill in Phase 6/9)* Single-expert curation (no inter-rater agreement
  process for the graph itself, unlike the weak-labeling pipeline's 88%
  coherence check — docs/DATA_QUALITY.md).
