"""OCD Knowledge Graph (Phase 9) — Layer 2 of the neuro-symbolic architecture.

`OCDGraph` wraps a `networkx.DiGraph` of the Phase 6 expert-curated content
(`configs/knowledge_graph/ocd_nodes.yaml`, `ocd_edges.yaml`; referenced via
`configs/knowledge_graph.yaml`). It answers "what is true in the OCD domain"
(query_treatment, explain_path) — never "what follows for this patient",
which is `src/rules_engine/verification.py::verify_recommendation`'s job
(Layer 3 reads Layer 2 facts, Layer 2 never reasons about a specific patient).

`networkx` over Neo4j is a deliberate stack decision
(docs/IMPLEMENTATION_PLAN.md §3, "Stack decisions"): ~40 nodes / ~50 edges
need no database, and an in-memory graph keeps the whole reasoning chain
debuggable in a Python REPL.

Consumed by `src/models/reasoning_pipeline.py` (Phase 9 orchestration) and
directly by the `/kg/query` and `/kg/explain_path` debug endpoints
(`src/api/main.py`).
"""

from __future__ import annotations

import networkx as nx

from .schema import Edge, Node


class OCDGraph:
    """Knowledge Graph for OCD clinical reasoning (Layer 2).

    Thin wrapper over `networkx.DiGraph`: nodes keyed by `Node.id`, edges
    carry `EdgeType` + `strength` as edge attributes. No caching, mutation,
    or inference lives here — see module docstring for the KG/Rules split.
    """

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    @classmethod
    def from_yaml(cls, nodes_yaml: str, edges_yaml: str) -> "OCDGraph":
        """Build a graph from the Phase 6 expert-curated YAML specs.

        Args:
            nodes_yaml: path to a nodes file shaped like
                `configs/knowledge_graph/ocd_nodes.yaml`.
            edges_yaml: path to an edges file shaped like
                `configs/knowledge_graph/ocd_edges.yaml`.

        Returns:
            An `OCDGraph` populated with every node/edge from the specs.

        Raises:
            FileNotFoundError: if either YAML is missing (Phase 6 not run
                yet) — callers should degrade the same way
                `RigidityEmbedder.load()` / `TemporalCFITransformer.load()`
                do for their missing checkpoints, not crash the API.
            ValueError: on a malformed spec (unknown NodeType/EdgeType,
                an edge referencing an undefined node id).
        """
        raise NotImplementedError

    def add_node(self, node: Node) -> None:
        """Insert or replace a node by `node.id`."""
        raise NotImplementedError

    def add_edge(self, edge: Edge) -> None:
        """Insert or replace a directed edge; both endpoints must already exist."""
        raise NotImplementedError

    def query_treatment(
        self,
        obsession: str,
        distortion: str,
        rigidity: float,
    ) -> dict:
        """Find the ERP protocol implied by an obsession + distortion + rigidity.

        Walks OBSESSION -> SYMPTOM -> DISTORTION -> CBT_TECHNIQUE ->
        ERP_PROTOCOL edges from `obsession`, filtered to paths that also
        touch `distortion`, and collects any CONTRAINDICATION nodes reachable
        from the resulting protocol. `rigidity` does not change *which*
        protocol is returned (that is graph structure, Layer 2's job) — it
        only affects `severity_recommendation`, matching the F2 invariant
        that rigidity modulates delivery, never confidence
        (docs/IMPLEMENTATION_PLAN.md §3, Layer 1.5).

        Args:
            obsession: a NodeType.OBSESSION id, e.g. "obsession_contamination".
            distortion: a NodeType.DISTORTION id, matching the taxonomy in
                `configs/data.yaml` (docs/TAXONOMY.md).
            rigidity: composite rigidity score in [0, 1]
                (`src/metrics/composite_rigidity.py`).

        Returns:
            {
                "protocol": str,               # ERP_PROTOCOL node id
                "steps": list[str],             # ordered CBT_TECHNIQUE ids
                "contraindications": list[str], # CONTRAINDICATION node ids
                "severity_recommendation": str, # gentler start if rigidity is high
            }
            or a not-found sentinel shape if no path connects obsession to a
            protocol — never raises for an unmatched-but-valid obsession id.

        Raises:
            KeyError: if `obsession` or `distortion` is not a known node id.
        """
        raise NotImplementedError

    def explain_path(self, start_node: str, end_node: str) -> list[tuple[str, str, str]]:
        """Return the reasoning chain from `start_node` to `end_node`.

        Powers the auditability guarantee in
        docs/IMPLEMENTATION_PLAN.md §3 (Layer 3 output: "why this protocol
        matches this obsession") and the `/kg/explain_path` debug endpoint.

        Args:
            start_node: a node id, typically an OBSESSION.
            end_node: a node id, typically an ERP_PROTOCOL.

        Returns:
            Ordered list of (from_node_id, edge_type_value, to_node_id)
            tuples along the shortest path. Empty list if no path exists.

        Raises:
            KeyError: if either node id is unknown.
        """
        raise NotImplementedError

    def get_node(self, node_id: str) -> Node | None:
        """Look up a node's full record (type + label + metadata), or None."""
        raise NotImplementedError

    def get_edge(self, from_id: str, to_id: str) -> Edge | None:
        """Look up a directed edge's full record, or None if it doesn't exist."""
        raise NotImplementedError


def build_graph(nodes_yaml: str, edges_yaml: str) -> OCDGraph:
    """Module-level convenience wrapper around `OCDGraph.from_yaml`.

    Exists so callers (and `configs/knowledge_graph.yaml`-driven loaders)
    can do `from src.knowledge_graph import build_graph` without knowing the
    class exists — same ergonomics as `src.models.reframing_dialogue.get_backend`.
    """
    raise NotImplementedError


def query_treatment(graph: OCDGraph, obsession: str, distortion: str, rigidity: float) -> dict:
    """Module-level convenience wrapper around `OCDGraph.query_treatment`."""
    raise NotImplementedError


def explain_path(graph: OCDGraph, start_node: str, end_node: str) -> list[tuple[str, str, str]]:
    """Module-level convenience wrapper around `OCDGraph.explain_path`."""
    raise NotImplementedError
