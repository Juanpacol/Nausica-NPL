"""Normalized paper record + dedup/ranking logic (pure, no network)."""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Paper:
    """A single scholarly work, normalized across sources."""

    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    citations: int = 0
    arxiv_id: str = ""
    pmid: str = ""
    sources: list[str] = field(default_factory=list)

    def dedup_key(self) -> str:
        """DOI when available, else normalized title."""
        if self.doi:
            return f"doi:{self.doi.lower()}"
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id.lower()}"
        return f"title:{normalize_title(self.title)}"

    def merge(self, other: "Paper") -> None:
        """Fold a duplicate record into this one, keeping the richest fields."""
        if len(other.abstract) > len(self.abstract):
            self.abstract = other.abstract
        if len(other.authors) > len(self.authors):
            self.authors = other.authors
        self.citations = max(self.citations, other.citations)
        self.doi = self.doi or other.doi
        self.arxiv_id = self.arxiv_id or other.arxiv_id
        self.pmid = self.pmid or other.pmid
        self.url = self.url or other.url
        self.venue = self.venue or other.venue
        self.year = self.year or other.year
        for src in other.sources:
            if src not in self.sources:
                self.sources.append(src)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "doi": self.doi,
            "url": self.url,
            "abstract": self.abstract,
            "citations": self.citations,
            "arxiv_id": self.arxiv_id,
            "pmid": self.pmid,
            "sources": self.sources,
        }

    def reference_line(self) -> str:
        """APA-ish one-line reference matching RESEARCH_FOCUS.md style."""
        if not self.authors:
            who = "[unknown authors]"
        elif len(self.authors) > 6:
            who = f"{_surname_first(self.authors[0])}, et al."
        else:
            who = "; ".join(_surname_first(a) for a in self.authors)
        year = f"({self.year})" if self.year else "(n.d.)"
        parts = [f"{who} {year}. {self.title.rstrip('.')}."]
        if self.venue:
            parts.append(f"*{self.venue}*.")
        if self.doi:
            parts.append(f"doi:{self.doi}")
        elif self.arxiv_id:
            parts.append(f"arXiv:{self.arxiv_id}")
        elif self.url:
            parts.append(self.url)
        return " ".join(parts)

    def bibtex(self) -> str:
        first_surname = _surname(self.authors[0]) if self.authors else "anon"
        key = re.sub(r"[^a-z0-9]", "", first_surname.lower()) + str(self.year or "")
        fields = {
            "title": self.title,
            "author": " and ".join(self.authors),
            "year": str(self.year or ""),
            "journal": self.venue,
            "doi": self.doi,
            "url": self.url or (f"https://arxiv.org/abs/{self.arxiv_id}" if self.arxiv_id else ""),
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        return f"@article{{{key},\n{body}\n}}"


_STOPWORDS = frozenset(
    "a an the of for in on with and or to from via its is are using based".split()
)


def normalize_title(title: str) -> str:
    """Lowercase, strip accents/punctuation — stable key for title dedup."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def _surname(author: str) -> str:
    author = author.strip()
    if "," in author:
        return author.split(",")[0].strip()
    return author.split()[-1] if author.split() else author


def _surname_first(author: str) -> str:
    """'Jane Q. Doe' -> 'Doe, J. Q.'; keeps 'Doe, Jane' order."""
    author = author.strip()
    if "," in author or not author:
        return author
    parts = author.split()
    if len(parts) == 1:
        return author
    initials = " ".join(f"{p[0]}." for p in parts[:-1])
    return f"{parts[-1]}, {initials}"


def keyword_overlap(query: str, paper: Paper) -> float:
    """Fraction of meaningful query terms found in the title + abstract."""
    terms = [
        t for t in normalize_title(query).split() if t not in _STOPWORDS and len(t) > 2
    ]
    if not terms:
        return 0.0
    haystack = normalize_title(paper.title + " " + paper.abstract)
    hits = sum(1 for t in terms if t in haystack)
    return hits / len(terms)


def score(paper: Paper, query: str) -> float:
    """Rank candidates: relevance gates influence.

    Citations only count in proportion to query overlap, so a mega-cited
    but unrelated classic cannot outrank a precise match. Corroboration
    across sources adds a small bonus.
    """
    overlap = keyword_overlap(query, paper)
    influence = math.log10(paper.citations + 1)
    corroboration = 0.5 * max(0, len(paper.sources) - 1)
    return overlap * (4.0 + influence) + corroboration


def dedup(papers: list[Paper]) -> list[Paper]:
    """Merge duplicates across sources; preserves first-seen order."""
    seen: dict[str, Paper] = {}
    # First pass: exact keys (DOI / arXiv / normalized title).
    for p in papers:
        key = p.dedup_key()
        if key in seen:
            seen[key].merge(p)
        else:
            seen[key] = p
    # Second pass: a DOI record and a title-only record of the same work.
    by_title: dict[str, Paper] = {}
    result: list[Paper] = []
    for p in seen.values():
        tkey = normalize_title(p.title)
        if tkey and tkey in by_title:
            by_title[tkey].merge(p)
        else:
            if tkey:
                by_title[tkey] = p
            result.append(p)
    return result
