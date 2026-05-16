#!/usr/bin/env bash
set -euo pipefail

cd /mnt/ntfs-disk/syk/sycophancy_guard
source ~/miniconda3/etc/profile.d/conda.sh
conda activate SFT

export PYTHONPATH=src:third_party/wildguard
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/dev/shm/hf_cache_wildguard_pku2k_full_20260508
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

INPUT=outputs/hard_v3_pku2k_full_contract_20260508/pku2k_core_only_wildguard.jsonl
OUTPUT_DIR=outputs/wildguard_pku2k_full_20260508
RESULTS=${OUTPUT_DIR}/results_wildguard_pku2k_core_only.jsonl
PREDICTIONS=${OUTPUT_DIR}/predictions_wildguard_pku2k_core_only.jsonl

mkdir -p "${OUTPUT_DIR}" "${HF_HOME}"

python -B -m sycophancy_guard.run_wildguard \
  --input "${INPUT}" \
  --output "${RESULTS}" \
  --backend auto \
  --device cuda \
  --batch-size 4 \
  --torch-dtype float16 \
  --max-new-tokens 128

python -B -m sycophancy_guard.wildguard_adapter \
  --items "${INPUT}" \
  --results "${RESULTS}" \
  --output "${PREDICTIONS}" \
  --target auto \
  --parse-error-policy fallback
