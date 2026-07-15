"""Pure-logic tests for litminer (no network, per project convention)."""

from pathlib import Path

import yaml

from src.litminer.models import Paper, dedup, keyword_overlap, normalize_title, score
from src.litminer.report import render_markdown
from src.litminer.search import Gap, GapResult

ROOT = Path(__file__).resolve().parents[1]


def _paper(**kw) -> Paper:
    base = dict(title="A Study of Things", authors=["Jane Doe"], year=2024)
    base.update(kw)
    return Paper(**base)


class TestNormalization:
    def test_normalize_title_strips_punctuation_and_case(self):
        assert normalize_title("MindMap: Knowledge-Graph Prompting!") == (
            "mindmap knowledge graph prompting"
        )

    def test_normalize_title_strips_accents(self):
        assert normalize_title("Depresión y Ansiedad") == "depresion y ansiedad"


class TestDedup:
    def test_same_doi_merges(self):
        a = _paper(doi="10.1/x", sources=["openalex"], citations=5)
        b = _paper(doi="10.1/X", sources=["crossref"], citations=9, abstract="long abstract")
        merged = dedup([a, b])
        assert len(merged) == 1
        assert merged[0].citations == 9
        assert merged[0].abstract == "long abstract"
        assert set(merged[0].sources) == {"openalex", "crossref"}

    def test_doi_record_absorbs_title_only_record(self):
        a = _paper(doi="10.1/x", sources=["crossref"])
        b = _paper(doi="", sources=["arxiv"], arxiv_id="2401.00001")
        merged = dedup([a, b])
        assert len(merged) == 1
        assert merged[0].doi == "10.1/x"
        assert merged[0].arxiv_id == "2401.00001"

    def test_different_titles_kept(self):
        merged = dedup([_paper(title="Alpha"), _paper(title="Beta")])
        assert len(merged) == 2


class TestRanking:
    def test_keyword_overlap_ignores_stopwords(self):
        p = _paper(title="Knowledge graph prompting elicits reasoning")
        assert keyword_overlap("the of knowledge graph", p) == 1.0

    def test_relevant_beats_famous(self):
        relevant = _paper(title="MindMap knowledge graph prompting LLM", citations=10)
        famous = _paper(title="Attention is all you need", citations=100000)
        q = "MindMap knowledge graph prompting large language models"
        assert score(relevant, q) > score(famous, q)


class TestReferenceFormatting:
    def test_reference_line_has_surname_year_doi(self):
        line = _paper(doi="10.1/x", venue="NeurIPS").reference_line()
        assert "Doe, J." in line
        assert "(2024)" in line
        assert "doi:10.1/x" in line

    def test_bibtex_valid_shape(self):
        entry = _paper(doi="10.1/x").bibtex()
        assert entry.startswith("@article{doe2024,")
        assert "title = {A Study of Things}" in entry


class TestConfig:
    def test_gap_registry_parses_and_is_well_formed(self):
        config = yaml.safe_load((ROOT / "configs" / "litminer.yaml").read_text())
        gaps = [Gap.from_dict(d) for d in config["gaps"]]
        assert len(gaps) >= 10
        ids = [g.id for g in gaps]
        assert len(ids) == len(set(ids)), "duplicate gap ids"
        for gap in gaps:
            assert gap.queries or gap.resolve, f"gap {gap.id} has nothing to do"
            assert gap.priority in {"critical", "high", "medium", "low"}


class TestReport:
    def test_render_markdown_orders_by_priority_and_flags_missing(self):
        low = GapResult(gap=Gap(id="b", title="Low gap", priority="low"))
        crit = GapResult(
            gap=Gap(id="a", title="Crit gap", priority="critical"),
            resolved=[{"id": "9999.99999", "type": "arxiv", "paper": None}],
            candidates=[_paper(doi="10.1/x")],
        )
        md = render_markdown([low, crit])
        assert md.index("Crit gap") < md.index("Low gap")
        assert "NOT FOUND" in md
        assert "Doe, J." in md
