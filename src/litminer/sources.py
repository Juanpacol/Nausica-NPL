"""Clients for public scholarly APIs.

Every source here is an official, documented, free API — no scraping.
Each client enforces a per-source minimum request interval and retries
politely on 429/5xx. Identify ourselves via User-Agent/mailto per each
API's etiquette guidelines.
"""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET

import requests

from .models import Paper

log = logging.getLogger("litminer")

_MAILTO = "juanpabloboteroespinosa@gmail.com"
_UA = f"nausica-litminer/0.1 (research literature review; mailto:{_MAILTO})"


class SourceClient:
    """Base: throttled GET with retries."""

    name = "base"
    min_interval = 1.0  # seconds between requests to this source

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = _UA
        self._last_request = 0.0

    def _get(self, url: str, params: dict | None = None, retries: int = 3) -> requests.Response | None:
        for attempt in range(retries):
            wait = self.min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                resp = self.session.get(url, params=params, timeout=30)
                self._last_request = time.monotonic()
            except requests.RequestException as exc:
                log.warning("%s: request failed (%s), attempt %d", self.name, exc, attempt + 1)
                time.sleep(2**attempt)
                continue
            if resp.status_code == 200:
                return resp
            if resp.status_code == 404:
                return None
            if resp.status_code in (429, 500, 502, 503):
                backoff = 2 ** (attempt + 1)
                log.warning("%s: HTTP %d, backing off %ds", self.name, resp.status_code, backoff)
                time.sleep(backoff)
                continue
            log.warning("%s: HTTP %d for %s", self.name, resp.status_code, url)
            return None
        return None

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        raise NotImplementedError


class OpenAlex(SourceClient):
    """https://docs.openalex.org — free, no key; mailto joins the polite pool."""

    name = "openalex"
    min_interval = 0.2

    _FIELDS = (
        "display_name,authorships,publication_year,primary_location,doi,"
        "cited_by_count,abstract_inverted_index,ids"
    )

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        resp = self._get(
            "https://api.openalex.org/works",
            {"search": query, "per-page": limit, "mailto": _MAILTO, "select": self._FIELDS},
        )
        if not resp:
            return []
        return [self._parse(w) for w in resp.json().get("results", [])]

    def _parse(self, w: dict) -> Paper:
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        ids = w.get("ids") or {}
        doi = (w.get("doi") or "").removeprefix("https://doi.org/")
        arxiv = ""
        if "arxiv.org" in (loc.get("landing_page_url") or ""):
            m = re.search(r"(\d{4}\.\d{4,5})", loc["landing_page_url"])
            arxiv = m.group(1) if m else ""
        return Paper(
            title=w.get("display_name") or "",
            authors=[
                a.get("author", {}).get("display_name", "")
                for a in (w.get("authorships") or [])
            ],
            year=w.get("publication_year"),
            venue=src.get("display_name") or "",
            doi=doi,
            url=ids.get("openalex", ""),
            abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
            citations=w.get("cited_by_count") or 0,
            arxiv_id=arxiv,
            sources=[self.name],
        )


class Crossref(SourceClient):
    """https://api.crossref.org — free; mailto param for the polite pool."""

    name = "crossref"
    min_interval = 1.0

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        resp = self._get(
            "https://api.crossref.org/works",
            {"query": query, "rows": limit, "mailto": _MAILTO},
        )
        if not resp:
            return []
        items = resp.json().get("message", {}).get("items", [])
        return [self._parse(it) for it in items]

    def resolve_doi(self, doi: str) -> Paper | None:
        resp = self._get(f"https://api.crossref.org/works/{doi}", {"mailto": _MAILTO})
        if not resp:
            return None
        return self._parse(resp.json().get("message", {}))

    def _parse(self, it: dict) -> Paper:
        year = None
        for key in ("published-print", "published-online", "issued"):
            parts = it.get(key, {}).get("date-parts", [[None]])
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        abstract = re.sub(r"<[^>]+>", " ", it.get("abstract", "")).strip()
        return Paper(
            title=(it.get("title") or [""])[0],
            authors=[
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in it.get("author", [])
            ],
            year=year,
            venue=(it.get("container-title") or [""])[0],
            doi=it.get("DOI", ""),
            url=it.get("URL", ""),
            abstract=abstract,
            citations=it.get("is-referenced-by-count") or 0,
            sources=[self.name],
        )


class SemanticScholar(SourceClient):
    """https://api.semanticscholar.org — free tier is a shared pool; go slow."""

    name = "semanticscholar"
    min_interval = 3.5  # unauthenticated shared limit is tight

    _FIELDS = "title,authors,year,venue,externalIds,citationCount,abstract,url"

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        resp = self._get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            {"query": query, "limit": limit, "fields": self._FIELDS},
        )
        if not resp:
            return []
        return [self._parse(p) for p in resp.json().get("data", [])]

    def _parse(self, p: dict) -> Paper:
        ext = p.get("externalIds") or {}
        return Paper(
            title=p.get("title") or "",
            authors=[a.get("name", "") for a in (p.get("authors") or [])],
            year=p.get("year"),
            venue=p.get("venue") or "",
            doi=ext.get("DOI", "") or "",
            url=p.get("url") or "",
            abstract=p.get("abstract") or "",
            citations=p.get("citationCount") or 0,
            arxiv_id=ext.get("ArXiv", "") or "",
            pmid=str(ext.get("PubMed", "") or ""),
            sources=[self.name],
        )


class Arxiv(SourceClient):
    """https://info.arxiv.org/help/api — Atom feed; 1 req / 3 s etiquette."""

    name = "arxiv"
    min_interval = 3.0
    _NS = {"atom": "http://www.w3.org/2005/Atom"}

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        resp = self._get(
            "https://export.arxiv.org/api/query",
            {"search_query": f"all:{query}", "max_results": limit},
        )
        return self._parse_feed(resp)

    def resolve_id(self, arxiv_id: str) -> Paper | None:
        resp = self._get(
            "https://export.arxiv.org/api/query", {"id_list": arxiv_id, "max_results": 1}
        )
        papers = self._parse_feed(resp)
        return papers[0] if papers else None

    def _parse_feed(self, resp: requests.Response | None) -> list[Paper]:
        if not resp:
            return []
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return []
        papers = []
        for entry in root.findall("atom:entry", self._NS):
            title = _text(entry, "atom:title", self._NS)
            if not title or title == "Error":
                continue
            raw_id = _text(entry, "atom:id", self._NS)
            m = re.search(r"abs/([\w.\-/]+?)(?:v\d+)?$", raw_id)
            published = _text(entry, "atom:published", self._NS)
            papers.append(
                Paper(
                    title=" ".join(title.split()),
                    authors=[
                        _text(a, "atom:name", self._NS)
                        for a in entry.findall("atom:author", self._NS)
                    ],
                    year=int(published[:4]) if published[:4].isdigit() else None,
                    venue="arXiv",
                    url=raw_id,
                    abstract=" ".join(_text(entry, "atom:summary", self._NS).split()),
                    arxiv_id=m.group(1) if m else "",
                    sources=[self.name],
                )
            )
        return papers


class EuropePMC(SourceClient):
    """https://europepmc.org/RestfulWebService — free; covers PubMed/MEDLINE."""

    name = "europepmc"
    min_interval = 1.0

    def search(self, query: str, limit: int = 8) -> list[Paper]:
        resp = self._get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            {
                "query": query,
                "format": "json",
                "pageSize": limit,
                "resultType": "core",
            },
        )
        if not resp:
            return []
        results = resp.json().get("resultList", {}).get("result", [])
        return [self._parse(r) for r in results]

    def _parse(self, r: dict) -> Paper:
        year = r.get("pubYear")
        return Paper(
            title=r.get("title", "").rstrip("."),
            authors=[a.strip() for a in r.get("authorString", "").rstrip(".").split(",") if a.strip()],
            year=int(year) if year and str(year).isdigit() else None,
            venue=r.get("journalTitle", "") or r.get("bookOrReportDetails", {}).get("publisher", ""),
            doi=r.get("doi", ""),
            url=f"https://europepmc.org/article/{r.get('source', 'MED')}/{r.get('id', '')}",
            abstract=r.get("abstractText", ""),
            citations=r.get("citedByCount") or 0,
            pmid=r.get("pmid", ""),
            sources=[self.name],
        )


def _reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex ships abstracts as {word: [positions]}; rebuild the text."""
    if not inverted:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inverted.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def _text(node: ET.Element, path: str, ns: dict) -> str:
    found = node.find(path, ns)
    return (found.text or "").strip() if found is not None else ""


ALL_SOURCES = {
    cls.name: cls for cls in (OpenAlex, Crossref, SemanticScholar, Arxiv, EuropePMC)
}
