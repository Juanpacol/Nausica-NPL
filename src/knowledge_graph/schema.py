"""Knowledge Graph schema (Phase 6/9) — OCD-specific node and edge vocabulary.

Layer 2's invariant (docs/IMPLEMENTATION_PLAN.md §3): this module holds
**declarative structure only** — what node/edge kinds exist and what metadata
they carry. No inference logic lives here or anywhere in `knowledge_graph/`;
conditional reasoning over these facts is `src/rules_engine/`'s job
(Layer 3). Keeping the split literal (KG = facts, Rules = inference over
facts) is what makes the two layers independently auditable.

Content (the actual ~40 nodes / ~50 edges) is hand-curated by an OCD/ERP
clinical expert in Phase 6 and lives in
`configs/knowledge_graph/ocd_nodes.yaml` / `ocd_edges.yaml` — never in this
file. This module only defines the *shape* that content must conform to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """OCD-specific node categories in the knowledge graph.

    Mirrors docs/IMPLEMENTATION_PLAN.md §3 (Layer 2 content): obsessions,
    symptoms, distortion patterns, CBT techniques, ERP protocols,
    contraindications, and patient state markers used to gate protocols.
    """

    OBSESSION = "obsession"
    SYMPTOM = "symptom"
    DISTORTION = "distortion"
    CBT_TECHNIQUE = "cbt_technique"
    ERP_PROTOCOL = "erp_protocol"
    CONTRAINDICATION = "contraindication"
    PATIENT_STATE = "patient_state"


class EdgeType(Enum):
    """Relationship types between nodes.

    Directed, matching the reasoning chain obsession -> symptom -> distortion
    -> technique -> protocol -> contraindication described in
    docs/IMPLEMENTATION_PLAN.md §3 (Layer 2 content). `strength` on the edge
    itself (see `Edge`) carries the curator's confidence in the relationship;
    the edge *type* only names what kind of relationship it is.
    """

    TRIGGERS = "triggers"  # obsession -> symptom
    MANIFESTS_AS = "manifests_as"  # symptom -> distortion
    ADDRESSED_BY = "addressed_by"  # distortion -> cbt_technique
    STEPS_IN = "steps_in"  # cbt_technique -> erp_protocol
    CONTRAINDICATES = "contraindicates"  # patient_state -> erp_protocol
    ESCALATES_TO = "escalates_to"  # patient_state -> patient_state (risk trajectory)


@dataclass(frozen=True)
class Node:
    """A single knowledge graph node.

    `id` is the stable key used everywhere (edges, query results,
    `explain_path` output, `configs/knowledge_graph/ocd_nodes.yaml` `id`
    field). `metadata` carries type-specific fields (e.g. `dsm5_code`,
    `severity_scale` for OBSESSION; `contraindication_reason` for
    CONTRAINDICATION) — deliberately untyped since the field set differs per
    NodeType and is clinician-curated content, not a code contract.
    """

    id: str
    type: NodeType
    label: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """A single directed knowledge graph edge.

    `strength` is the curator's confidence in the relationship, in [0, 1]
    (see `configs/knowledge_graph/ocd_edges.yaml`) — used by
    `OCDGraph.query_treatment` to rank competing paths, never to imply a
    learned/statistical weight.
    """

    from_id: str
    to_id: str
    type: EdgeType
    strength: float = 1.0
    metadata: dict = field(default_factory=dict)
