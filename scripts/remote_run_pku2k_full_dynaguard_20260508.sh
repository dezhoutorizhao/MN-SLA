#!/usr/bin/env bash
set -euo pipefail

cd /mnt/ntfs-disk/syk/sycophancy_guard
source ~/miniconda3/etc/profile.d/conda.sh
conda activate SFT

export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/dev/shm/hf_cache_dynaguard_pku2k_full_20260508
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

INPUT=outputs/hard_v3_pku2k_full_contract_20260508/pku2k_core_only_messages.jsonl
OUTPUT_DIR=outputs/dynaguard_pku2k_full_20260508
OUTPUT=${OUTPUT_DIR}/predictions_dynaguard_pku2k_core_only.jsonl

mkdir -p "${OUTPUT_DIR}" "${HF_HOME}"

python -B -m sycophancy_guard.run_dynaguard \
  --input "${INPUT}" \
  --output "${OUTPUT}" \
  --device cuda \
  --torch-dtype bfloat16 \
  --batch-size 4 \
  --max-new-tokens 16 \
  --parse-error-policy fallback
