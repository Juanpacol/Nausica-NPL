"""Layer 2 — Knowledge Graph (Phase 9). See docs/KG_SPECIFICATION.md.

Public surface: build a graph from the Phase 6 expert-curated YAML specs,
then query it for treatment paths and their supporting reasoning chain.
Everything else (`OCDGraph` internals, `schema.Node`/`Edge`) is an
implementation detail callers shouldn't need to reach for.
"""

from __future__ import annotations

from .ocd_graph import OCDGraph, build_graph, explain_path, query_treatment
from .schema import EdgeType, NodeType

__all__ = [
    "build_graph",
    "query_treatment",
    "explain_path",
    "NodeType",
    "EdgeType",
    "OCDGraph",
]
