#!/usr/bin/env bash
set -euo pipefail

cd /mnt/ntfs-disk/syk/sycophancy_guard
source ~/miniconda3/etc/profile.d/conda.sh
conda activate SFT

export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/dev/shm/hf_cache_dynaguard_nonpku_20260507
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

mkdir -p outputs/dynaguard_non_pku_harmbench_xstest_200base_20260507 logs "$HF_HOME"

python -B -m sycophancy_guard.run_dynaguard \
  --input outputs/hard_v3_non_pku_harmbench_xstest_200base_20260507/hard_v3_contract_subset_200base_core_only_messages.jsonl \
  --output outputs/dynaguard_non_pku_harmbench_xstest_200base_20260507/predictions_dynaguard_non_pku_200base_core_only.jsonl \
  --device cuda \
  --torch-dtype bfloat16 \
  --batch-size 4 \
  --max-new-tokens 16 \
  --parse-error-policy fallback
