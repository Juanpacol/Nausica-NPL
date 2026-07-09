"""Download the three source datasets from HuggingFace into data/raw/.

Usage: python -m src.data_pipeline.download_datasets
Datasets and licenses: docs/LICENSING.md. Raw data is gitignored — never commit it.
"""

from datasets import load_dataset

from src.utils.config import PROJECT_ROOT, load_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def download_all() -> dict[str, str]:
    cfg = load_config("data")["datasets"]
    results = {}
    for name, spec in cfg.items():
        target = PROJECT_ROOT / spec["local_dir"]
        if target.exists() and any(target.iterdir()):
            logger.info("%s already present at %s, skipping", name, target)
            results[name] = "cached"
            continue
        logger.info("Downloading %s (%s) ...", name, spec["hf_id"])
        try:
            # data_files pins a specific file when a repo mixes incompatible schemas
            kwargs = {"data_files": spec["data_files"]} if "data_files" in spec else {}
            ds = load_dataset(spec["hf_id"], **kwargs)
            target.mkdir(parents=True, exist_ok=True)
            ds.save_to_disk(str(target))
            sizes = {split: len(ds[split]) for split in ds}
            logger.info("  saved %s: %s", name, sizes)
            results[name] = f"ok {sizes}"
        except Exception as e:  # noqa: BLE001 — report per-dataset, keep going
            logger.error("  FAILED %s: %s", name, e)
            results[name] = f"error: {e}"
    return results


if __name__ == "__main__":
    summary = download_all()
    print("\n=== Download summary ===")
    for name, status in summary.items():
        print(f"  {name}: {status}")
