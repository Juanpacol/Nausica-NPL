#!/usr/bin/env bash
# Phase 1 data pipeline orchestrator: raw datasets -> trained distortion classifier.
#
# Usage:
#   ./scripts/run_data_pipeline.sh            # full run
#   ./scripts/run_data_pipeline.sh --dry-run  # cap weak labeling at 50 rows (cheap smoke test)
#
# Steps (each script is idempotent / resumable on its own):
#   1. download_datasets            HF datasets -> data/raw/
#   2. preprocessing consolidate    data/raw/ -> data/processed/texts.jsonl
#   3. weak_labeling                texts.jsonl -> weak_labeled.jsonl (+ spot-check sample)
#   *  MANUAL GATE: review the spot-check sample, fill docs/DATA_QUALITY.md.
#      The full run stops here on purpose; pass --skip-gate only after the review.
#   4. preprocessing split          weak_labeled.jsonl -> train/val/test.jsonl
#   5. distortion_classifier train  -> results/distortion_classifier/final
set -euo pipefail
cd "$(dirname "$0")/.."

LIMIT_ARGS=()
SKIP_GATE=false
for arg in "$@"; do
  case "$arg" in
    --dry-run)   LIMIT_ARGS=(--limit 50); SKIP_GATE=true ;;
    --skip-gate) SKIP_GATE=true ;;
    *) echo "Unknown flag: $arg (use --dry-run or --skip-gate)"; exit 1 ;;
  esac
done

echo "== [1/5] Downloading datasets =="
python -m src.data_pipeline.download_datasets

echo "== [2/5] Consolidating raw texts =="
python -m src.data_pipeline.preprocessing consolidate

echo "== [3/5] Weak labeling (LLM-as-annotator) =="
python -m src.data_pipeline.weak_labeling \
  --input data/processed/texts.jsonl \
  --output data/processed/weak_labeled.jsonl \
  ${LIMIT_ARGS[@]+"${LIMIT_ARGS[@]}"}

if [ "$SKIP_GATE" = false ]; then
  cat <<'EOF'

== MANUAL GATE ==
Review data/processed/weak_labeled_spotcheck.jsonl against docs/TAXONOMY.md and
record per-label agreement in docs/DATA_QUALITY.md. If any label agrees < 80%,
fix the few-shot prompt in src/data_pipeline/weak_labeling.py and re-run step 3.

Then resume with:  ./scripts/run_data_pipeline.sh --skip-gate
EOF
  exit 0
fi

echo "== [4/5] Splitting train/val/test =="
python -m src.data_pipeline.preprocessing split

echo "== [5/5] Fine-tuning distortion classifier =="
python -m src.models.distortion_classifier train

echo "Done. Checkpoint: results/distortion_classifier/final"
