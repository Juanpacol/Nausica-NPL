"""Orchestrator: run each gap's queries across sources, merge, rank, cache."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .models import Paper, dedup, score
from .sources import ALL_SOURCES, Arxiv, Crossref, SourceClient

log = logging.getLogger("litminer")


@dataclass
class Gap:
    """One research gap to fill, loaded from configs/litminer.yaml."""

    id: str
    title: str
    priority: str = "medium"
    need: str = ""
    queries: list[str] = field(default_factory=list)
    resolve: list[dict] = field(default_factory=list)  # [{type: arxiv|doi, id: ...}]

    @classmethod
    def from_dict(cls, d: dict) -> "Gap":
        return cls(
            id=d["id"],
            title=d.get("title", d["id"]),
            priority=d.get("priority", "medium"),
            need=d.get("need", ""),
            queries=d.get("queries", []),
            resolve=d.get("resolve", []),
        )


@dataclass
class GapResult:
    gap: Gap
    candidates: list[Paper] = field(default_factory=list)
    resolved: list[dict] = field(default_factory=list)  # [{"query": id, "paper": Paper|None}]


class Cache:
    """Flat JSON cache so re-runs don't re-hit the APIs."""

    def __init__(self, path: Path, enabled: bool = True):
        self.path = path
        self.enabled = enabled
        self._data: dict[str, list[dict]] = {}
        if enabled and path.exists():
            try:
                self._data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                log.warning("cache unreadable, starting fresh: %s", path)

    def get(self, key: str) -> list[Paper] | None:
        if not self.enabled or key not in self._data:
            return None
        return [Paper(**d) for d in self._data[key]]

    def put(self, key: str, papers: list[Paper]) -> None:
        if not self.enabled:
            return
        self._data[key] = [p.to_dict() for p in papers]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=1))


class Miner:
    def __init__(
        self,
        source_names: list[str] | None = None,
        cache: Cache | None = None,
        per_query: int = 8,
        top_k: int = 10,
    ):
        names = source_names or list(ALL_SOURCES)
        self.sources: list[SourceClient] = [ALL_SOURCES[n]() for n in names]
        self.cache = cache
        self.per_query = per_query
        self.top_k = top_k

    def _cached_search(self, client: SourceClient, query: str) -> list[Paper]:
        key = f"{client.name}::search::{query}::{self.per_query}"
        if self.cache and (hit := self.cache.get(key)) is not None:
            return hit
        papers = client.search(query, limit=self.per_query)
        if self.cache:
            self.cache.put(key, papers)
        return papers

    def run_gap(self, gap: Gap) -> GapResult:
        result = GapResult(gap=gap)

        # 1) Direct resolution of partial/known identifiers (verification mode).
        for item in gap.resolve:
            paper = self._resolve(item)
            result.resolved.append(
                {"id": item.get("id", ""), "type": item.get("type", ""), "paper": paper}
            )

        # 2) Query search across all sources.
        raw: list[Paper] = []
        for query in gap.queries:
            for client in self.sources:
                found = self._cached_search(client, query)
                log.info("  %s: %d results for %r", client.name, len(found), query)
                raw.extend(found)

        merged = dedup(raw)
        # Rank against the union of queries so multi-query gaps don't bias
        # toward whichever query ran last.
        joined = " ".join(gap.queries)
        merged.sort(key=lambda p: score(p, joined), reverse=True)
        result.candidates = merged[: self.top_k]
        return result

    def _resolve(self, item: dict) -> Paper | None:
        kind, ident = item.get("type"), item.get("id", "")
        key = f"resolve::{kind}::{ident}"
        if self.cache and (hit := self.cache.get(key)) is not None:
            return hit[0] if hit else None
        paper: Paper | None = None
        if kind == "arxiv":
            client = next((s for s in self.sources if isinstance(s, Arxiv)), Arxiv())
            paper = client.resolve_id(ident)
        elif kind == "doi":
            client = next((s for s in self.sources if isinstance(s, Crossref)), Crossref())
            paper = client.resolve_doi(ident)
        else:
            log.warning("unknown resolve type %r", kind)
        if self.cache:
            self.cache.put(key, [paper] if paper else [])
        return paper
