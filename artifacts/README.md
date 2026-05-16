# Public Aggregate Artifacts

This directory mirrors a curated subset of local `outputs/` for public review.
It contains aggregate diagnostics, tables, claim-gate summaries, and JSON/CSV
reports used by the paper. It intentionally excludes raw rendered benchmark
prompts, prediction JSONL files, local-only annotation packets, private answer
keys, model caches, and weights.

## Included Groups

- `hard_v3_method_claim_gate_20260501`: final selected-main claim-gate summary.
- `mn_sla_gated_20260509`: neutral-consensus selective-wrapper aggregate replay.
- `neutral_control_validity_audit_20260508`: aggregate mechanical validity checks.
- `hard_v3_breakdowns_20260501`: family/layout/direction breakdown summaries.
- `hard_v3_slice_inference_20260501`: slice-localization inference tables.
- `hard_v3_local_audit_20260507`: local projection and sensitivity audit summaries.
- `projection_ablation_20260507`: no-inference projection ablation summaries.
- `hard_v3_pku2k_full_contract_20260508`: PKU2K contract-level aggregate audit.
- `hard_v3_non_pku_harmbench_xstest_200base_20260507`: non-PKU aggregate audit.
- `pku2k_full_diagnostic_analysis_20260508`: safe aggregate tarball for the
  DynaGuard PKU2K diagnostic analysis.

## Claim Boundary

These artifacts support a narrow MN-SLA audit claim: raw pressure-gap replication
and matched-control attenuation under a fail-closed artifact contract. They do
not support broad SOTA, equal-cost deployment, single-pass robustness, residual
elimination at scale for mean-v1, or completed human semantic validation.
