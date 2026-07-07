"""Central config loading. All tunables live in configs/*.yaml, not in code."""

from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


@lru_cache(maxsize=None)
def load_config(name: str) -> dict:
    """Load configs/<name>.yaml (cached)."""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def taxonomy_labels() -> list[str]:
    return load_config("data")["taxonomy"]["labels"]


def cfi_weights() -> dict[str, float]:
    return load_config("data")["cfi_weights"]
