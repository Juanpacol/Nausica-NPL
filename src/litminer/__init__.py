"""litminer — automated literature sourcing for research gap coverage.

Queries legitimate scholarly APIs (OpenAlex, Crossref, Semantic Scholar,
arXiv, Europe PMC) to find and verify references for the gaps declared in
``configs/litminer.yaml``. No scraping: every source is an official,
public, rate-limited API.

Usage:
    python -m src.litminer                     # run all gaps
    python -m src.litminer --gap trustmh-bench # run one gap
    python -m src.litminer --list              # list configured gaps
"""

__version__ = "0.1.0"
