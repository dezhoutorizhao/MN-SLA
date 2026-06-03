# MN-SLA 实验设置与实验结果总报告：对应 NeurIPS / AAAI 路线图

生成日期：2026-06-03  
对应设计文档：

- `MN-SLA_NeurIPS_MainTrack_Spotlight_实验推进路线图.md`
- `MN-SLA后续稳拿AAAI_MainTrack实验计划.md`

本报告汇总当前工作区中所有与 MN-SLA NeurIPS main-track / spotlight 以及 AAAI main-track / spotlight 计划相关的实验设置、实际执行结果、证据路径和 claim 边界。报告只引用 aggregate-level 产物，不包含 raw rendered prompt text、私有答案 key、annotation packet 原文、模型缓存或数据原文。

## 0. 总体结论

最终路线图审计：

```text
outputs/mn_sla_roadmap_completion_audit_20260602/roadmap_completion_audit.json
outputs/mn_sla_roadmap_completion_audit_20260602/roadmap_completion_audit.md
```

当前结论：

```text
completion_verdict = ALL_COMPLETE
milestone_a = completed
milestone_b = completed
```

其中：

- Milestone A：NeurIPS main-track minimum experimental package 已完成。
- Milestone B：spotlight recommended experimental package 已在 narrow, aggregate-only claim boundaries 下完成。
- 该结论不等于 deployable defense、不等于 universal source-general robustness、不等于 broad guard-family certification，也不等于公开 raw prompts。

最终 E1-E9 状态：

| ID | NeurIPS / Spotlight 实验 | 当前状态 | 核心证据 |
|---|---|---|---|
| E1 | Independent overlapping human IAA | `completed_expanded_270_human_iaa` | `outputs/human_validation_expanded_20260603/analysis_completed/fail_closed_report.json` |
| E2 | Main-panel baseline expansion | `completed_spotlight_baseline_breadth` | `outputs/mn_sla_completion_and_release_audit_20260602/baseline_ledger.csv` |
| E3 | Preregistered estimator x neutral-template robustness | `completed_spotlight_3template_grid` | `outputs/mn_sla_roadmap_completion_audit_20260602/e3_preregistered_template_grid_summary.csv` |
| E4 | Simple-baseline wrong-conclusion matrix | `completed_aggregate_matrix` | `outputs/mn_sla_roadmap_completion_audit_20260602/e4_wrong_conclusion_matrix.csv` |
| E5 | External open-dataset expansion | `completed_external_sources_with_confounding_model` | `outputs/qwen3guard_beavertails500_20260603/qwen3guard_beavertails500_threshold_summary.json`; `outputs/mn_sla_roadmap_completion_audit_20260602/e5_source_label_confounding_audit.json` |
| E6 | Probability / logit robustness upgrade | `completed_two_score_guard_families_with_external` | `outputs/e6_score_level_analysis_20260603/e6_score_level_summary.json` |
| E7 | Power curve and sample-size sensitivity | `completed_three_baseline_power_curves` | DynaGuard / WildGuard / Qwen3Guard power-curve summaries |
| E8 | Slice denominator + uncertainty audit | `completed_existing_slice_audit` | `outputs/mn_sla_roadmap_completion_audit_20260602/e8_slice_denominator_uncertainty_audit.csv` |
| E9 | Release / reproducibility package | `completed_public_aggregate_package` | `outputs/mn_sla_public_aggregate_package_20260602` |

## 1. 两份设计文档的一一对应关系

| NeurIPS 路线图 / 治理项 | AAAI 计划对应项 | 设计目标 | 当前完成状态 |
|---|---|---|---|
| E1 Independent overlapping human IAA | P0-1 Overlapping human validation / IAA | 验证 matched neutral controls 的 label preservation、difficulty preservation、pressure cue removal、desired-label cue removal | 完成 270-item expanded IAA |
| E2 Main-panel baseline expansion | P1-1 Broader baseline family expansion | 扩展 main-panel compatible baselines，避免只依赖 DynaGuard/WildGuard | 完成 5 个 formal/main-compatible baselines + 1 supplementary |
| E3 Estimator x neutral-template robustness | P0-4 Estimator x neutral-template robustness | 预注册 estimator/template grid，验证主结论跨模板/估计器稳定性 | 完成 3-template x 5-estimator x 3 formal baselines |
| E4 Wrong-conclusion matrix | P0-2 Simple-baseline comparison | 证明 naive comparator 会产生 inflated 或错误结论，从而证明 MN-SLA 必要性 | 完成 aggregate matrix |
| E5 External open-dataset expansion | P0-3 External open-dataset replication | BeaverTails 与 Non-PKU source-pair 外部证据，处理 source/label confounding | 完成 external + confounding-modeled evidence |
| E6 Probability / logit robustness | P0-5 Threshold / probability-level robustness | 不只看 hard label，加入 score/logit/probability drift 与 calibration | 完成 Qwen3Guard + HarmAug 两个 score/probability guard families |
| E7 Power curve | P0-6 Scale-aware gate 的 empirical support / AAAI scale-aware empirical study | 说明样本量对 raw gap、residual、attenuation detection 的影响 | 完成 3 baseline power curves |
| E8 Slice denominator + uncertainty audit | P1-3 Slice stability and denominator reporting | 避免 low-N slice 和多重检验导致过度解释 | 完成 168-row slice audit |
| E9 Release / reproducibility package | P1-2 Raw-prompt auditability / safe release policy | 公开 aggregate-only package、hash manifest、scanner report、deny-by-default policy | 完成 public aggregate package |
| NeurIPS P0-6 Scale-aware gate variant | AAAI P0-6 Scale-aware gate variant | 形成 allowed/disallowed claim matrix | 已作为 claim matrix / governance 完成 |
| 无直接 E 编号 | P1-4 Multi-cultural / language pressure cue pilot | 可选 societal-impact / cross-lingual pilot | 未计入当前 ALL_COMPLETE 审计；当前未发现正式完成产物 |

说明：P1-4 是 AAAI 计划中明确写为“不是 main-track 必需，但对 spotlight 和 societal-impact 有价值”的可选扩展。当前 `ALL_COMPLETE` 是 NeurIPS / spotlight recommended experimental package 的完成结论，不把 P1-4 写成已完成。

## 2. Claim 边界

当前可以安全写：

> MN-SLA is a human-validated, matched-neutral audit protocol showing that social-pressure sensitivity is a distinct failure mode not captured by ordinary F1. Same-base matched controls are necessary; raw pressure gaps replicate across PKU and BeaverTails; score/logit diagnostics and robustness audits support a spotlight-level aggregate evidence package under narrow claim boundaries.

必须避免：

- 不写 “MN-SLA is a deployable defense.”
- 不写 “neutralization eliminates residual pressure sensitivity.”
- 不写 “all guards are robust under all neutral templates.”
- 不写 “universal source-general robustness.”
- 不写 “broad guard-family certification.”
- 不公开 raw prompts、private answer key、local-only annotation packet、unreviewed JSONL ledgers、model caches。

## 3. E1 / P0-1：Independent Overlapping Human IAA

### 3.1 原设计

NeurIPS 路线图要求：

- 最小版：90 annotation items、30 matched cells、2 annotators、fail-closed pass。
- Spotlight 版：180-270 overlap items、2-3 annotators、kappa/PABAK/CI clear。

AAAI 计划要求：

- 至少 2 名 independent human annotators。
- 标注字段包含 label、difficulty、pressure cue、desired-label cue、unannotatable、quality flag。
- 指标包括 neutral-clean label agreement、difficulty preserved、pressure cue removal、desired-label cue removal、attack cue present、IAA。

### 3.2 实际设置

当前使用 expanded 270-item packet：

| 项目 | 实际设置 |
|---|---:|
| packet | `outputs/human_validation_expanded_20260603` |
| annotated_items | 270 |
| matched cells | 90 |
| roles per cell | attack / clean / neutral |
| role counts | attack 90, clean 90, neutral 90 |
| regimes | `non_pku200_source_pair`, `pku200_scale`, `pku50_main_gate` |
| cells per regime | 30 / 30 / 30 |
| annotators | `ann_a`, `ann_b` |
| analyzer | `scripts/analyze_expanded_human_iaa_20260603.py` |

标注文件：

```text
outputs/human_validation_expanded_20260603/annotations_ann_a.csv
outputs/human_validation_expanded_20260603/annotations_ann_b.csv
```

结果输出：

```text
outputs/human_validation_expanded_20260603/analysis_completed/fail_closed_report.json
outputs/human_validation_expanded_20260603/analysis_completed/human_annotation_analysis_summary.json
outputs/human_validation_expanded_20260603/analysis_completed/human_annotation_analysis_summary.md
outputs/human_validation_expanded_20260603/analysis_completed/iaa_pairwise.csv
```

### 3.3 Fail-closed 阈值与结果

| 指标 | 阈值 | 结果 | 状态 |
|---|---:|---:|---|
| min annotators per item | 2 | 2 | pass |
| annotated_items | 270 | 270 | pass |
| complete_cells | 90 | 90 | pass |
| complete_cells_by_regime | 30/30/30 | 30/30/30 | pass |
| item_label_match_rate | >= 0.90 | 0.90 | pass, 刚好达标 |
| neutral_clean_label_agreement_rate | >= 0.90 | 1.00 | pass |
| difficulty_preserved_rate | >= 0.90 | 1.00 | pass |
| neutral_pressure_removed_rate | >= 0.95 | 1.00 | pass |
| neutral_desired_label_absent_rate | >= 0.95 | 1.00 | pass |
| attack_pressure_present_rate | >= 0.90 | 1.00 | pass |

### 3.4 IAA 结果

| 字段 | exact agreement | kappa | PABAK | 其他 |
|---|---:|---:|---:|---|
| label_choice | 270/270 = 1.000 | 1.000 | 1.000 | Wilson CI low = 0.986 |
| desired_label_cue | 270/270 = 1.000 | 1.000 | 1.000 | Wilson CI low = 0.986 |
| pressure_cue_binary | 270/270 = 1.000 | 1.000 | 1.000 | Wilson CI low = 0.986 |
| pressure_cue_exact | 230/270 = 0.852 | 0.778 | NA | 细粒度 cue 强弱有分歧，但 binary cue 无分歧 |
| difficulty_1_5 | 241/270 = 0.893 | NA | NA | Spearman = 0.958, within-1 = 270/270 |

### 3.5 解释

该实验完成 NeurIPS E1 和 AAAI P0-1 的 spotlight 版要求。可写 “blinded sample-level human validation passed fail-closed thresholds”。不能把它写成 universal neutral-control validity 或机制层面的 robustness proof。

## 4. E2 / P1-1：Main-panel Baseline Expansion

### 4.1 原设计

NeurIPS E2 要求：

- main-track 最低：至少 4 formal baselines，或 3 formal + 2 strong diagnostics。
- spotlight 建议：5-6 compatible baselines 或更广 formal main-panel coverage。

AAAI P1-1 要求：

- 扩展 baseline family。
- main-panel inclusion criteria 包括 source availability、direct contract compatibility、parser/exclusion audit、prediction ledger。

### 4.2 实际 baseline ledger

证据：

```text
outputs/mn_sla_completion_and_release_audit_20260602/baseline_ledger.csv
```

| Baseline | 类别 | 当前状态 | Claim 边界 |
|---|---|---|---|
| DynaGuard | dynamic policy guard | `evaluated` | aggregate diagnostic/confirmatory scope |
| WildGuard | open moderation guard | `evaluated` | aggregate diagnostic/confirmatory scope |
| Qwen3Guard | probability/logit guard | `evaluated_score_logit` | score/logit baseline, not broad certification |
| HarmAug | distilled probability guard | `evaluated_score_probability` | score/probability baseline, not broad certification |
| BingoGuard | open moderation guard | `evaluated` | aggregate diagnostic/confirmatory scope |
| ShieldLM | open moderation guard | `supplementary_only` | supplementary contract evidence only |
| LlamaGuard | open moderation guard | `runner_available_no_formal_run` | 不计入 formal result |
| NemotronGuard | open moderation guard | `runner_available_no_formal_run` | 不计入 formal result |
| ShieldGemma | open moderation guard | `runner_available_no_formal_run` | 不计入 formal result |
| OpenAI Moderation API | external API | `excluded` | 需单独 protocol |
| Perspective API | external API | `excluded` | 需单独 protocol |

### 4.3 Spotlight baseline breadth 结果

最终 E2 状态：

```text
completed_spotlight_baseline_breadth
```

当前计数：

- 5 个 formal/main-compatible baselines：DynaGuard、WildGuard、Qwen3Guard、HarmAug、BingoGuard。
- 1 个 supplementary baseline：ShieldLM。
- 0 个仅 diagnostic baseline，因为 HarmAug 已由 E6 score-level evidence 升级为 `evaluated_score_probability`。

HarmAug 升级依据：

```text
outputs/harmaug_pku200_20260602/predictions_harmaug_pku200_core_only_full.jsonl
outputs/harmaug_beavertails200_20260602/predictions_harmaug_beavertails200_core_only_full.jsonl
```

该升级只表示 HarmAug 有 PKU200 + BeaverTails200 score/probability baseline evidence，不表示 broad guard-family certification。

## 5. E4 / P0-2：Simple-baseline Wrong-conclusion Matrix

### 5.1 原设计

NeurIPS E4 和 AAAI P0-2 的目标都是证明 MN-SLA 不是一个可有可无的复杂设计，而是必要的 matched-control protocol。对比对象包括：

- attack-vs-clean / raw pressure gap
- clean carry-forward proxy
- attack-vs-base-neutral
- attack-vs-generic/global-neutral
- attack-vs-other-base-neutral
- wrong-layout same-base neutral
- MN-SLA matched neutral

### 5.2 核心早期结果：raw gap vs matched residual

| Dataset | Guard | Raw gap | Matched mean residual | Global neutral | Other-base | Matched attenuation |
|---|---|---:|---:|---:|---:|---:|
| PKU200 | DynaGuard | 0.134948 | 0.007542 | 0.321208 | 0.321208 | 0.127406 |
| PKU200 | WildGuard | 0.028281 | 0.003750 | 0.286250 | 0.286250 | 0.024531 |
| PKU2K | DynaGuard | 0.117500 | 0.006562 | 0.252937 | 0.252937 | 0.110937 |
| PKU2K | WildGuard | 0.021344 | 0.002000 | 0.267625 | 0.267625 | 0.019344 |
| BeaverTails200 | DynaGuard | 0.158750 | 0.009375 | 0.235625 | 0.235625 | 0.149375 |
| BeaverTails200 | WildGuard | 0.033438 | 0.003125 | 0.159375 | 0.159375 | 0.030313 |

### 5.3 Wrong-conclusion matrix 结果

证据：

```text
outputs/mn_sla_roadmap_completion_audit_20260602/e4_wrong_conclusion_matrix.csv
outputs/mn_sla_roadmap_completion_audit_20260602/e4_wrong_conclusion_matrix.md
```

结果：

| 项目 | 数值 |
|---|---:|
| comparator rows | 72 |
| verdict mismatches vs MN-SLA matched_mean | 33 |
| abs inflation ratio >= 5 | 32 |
| max abs inflation ratio | 172 |

代表性例子：

| Dataset | Guard | Comparator | Comparator gap | Matched gap | Inflation | Verdict mismatch |
|---|---|---|---:|---:|---:|---|
| BeaverTails200 | BingoGuard | attack-vs-clean/raw | 0.024688 | -0.001250 | -19.75 | true |
| BeaverTails200 | BingoGuard | global-neutral | 0.215000 | -0.001250 | -172.00 | true |
| BeaverTails200 | DynaGuard | attack-vs-clean/raw | 0.158750 | 0.009375 | 16.93 | false |
| BeaverTails200 | DynaGuard | clean carry-forward | -0.039375 | 0.009375 | -4.20 | true |

解释：常见 naive comparator 不是单纯噪声更大，而是会回答不同 estimand，并在许多条件下给出 inflated 或错误结论。这支持 MN-SLA same-base matched-neutral 设计的必要性。

## 6. E5 / P0-3：External Open-dataset Expansion

### 6.1 原设计

NeurIPS E5 和 AAAI P0-3 要求：

- 至少 BeaverTails200 + 一个额外 external source 或 BeaverTails500。
- spotlight 要求 3+ datasets，或显式处理 source/label confounding。
- 失败或混合时必须写成 source/contract-dependent，不写 universal robustness。

### 6.2 实际设置与结果

证据：

```text
outputs/qwen3guard_beavertails500_20260603/qwen3guard_beavertails500_threshold_summary.json
outputs/mn_sla_roadmap_completion_audit_20260602/e5_source_label_confounding_audit.json
outputs/mn_sla_roadmap_completion_audit_20260602/e5_source_label_confounding_matrix.csv
```

状态：

```text
completed_external_sources_with_confounding_model
```

Non-PKU source-pair 设置：

| Source | Label | Bases |
|---|---|---:|
| AlignmentResearch/HarmBench | unsafe | 100 |
| XSTest v2 | safe | 100 |

E5 confounding audit：

| 项目 | 结果 |
|---|---|
| n_bases | 200 |
| n_sources | 2 |
| n_labels | 2 |
| source_label_confounding | `complete_source_label_binding_modeled` |
| status | `completed_confounding_modeled_source_pair` |

解释：E5 满足 spotlight 级 external/source evidence 的要求，但必须写成 confounding-modeled source-pair diagnostic。不能写成 universal source-general robustness。

## 7. E3 / P0-4：Preregistered Estimator x Neutral-template Robustness

### 7.1 原设计

NeurIPS E3 和 AAAI P0-4 要求：

- fresh / holdout split，避免 Gate-50 或 template-authoring base ids。
- 至少 3 neutral templates。
- 5 个 estimator variants。
- 至少 3 formal baselines 满足 3-template coverage。
- 不要求所有 guard 都 positive attenuation，而是报告主结论是否稳定以及 guard-specific behavior。

实际 estimator family：

```text
mean-v1, median-v1, trimmed-mean-v1, first-neutral-v1, majority-neutral-v1
```

实际 neutral templates：

```text
neutral_careful_review
neutral_format_reminder
neutral_policy_restated
```

### 7.2 最终结果

证据：

```text
outputs/mn_sla_roadmap_completion_audit_20260602/e3_preregistered_template_grid_summary.csv
outputs/mn_sla_roadmap_completion_audit_20260602/e3_preregistered_template_grid_summary.md
```

最终状态：

```text
completed_spotlight_3template_grid
```

3-template formal guard coverage：

| Run | Formal guard | Bases | Neutral templates | Estimators | Combinations | Attenuation positive rate | Median attenuation | Median residual gap | Spotlight template target |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| dynaguard_beavertails200_3neutral | DynaGuard | 200 | 3 | 5 | 20 | 1.000 | 0.039375 | 0.158750 | yes |
| qwen3guard_beavertails500_3neutral | Qwen3Guard | 500 | 3 | 5 | 20 | 0.500 | -0.000250 | 0.046250 | yes |
| wildguard_beavertails200_3neutral | WildGuard | 200 | 3 | 5 | 20 | 0.000 | -0.013750 | 0.037813 | yes |

Additional diagnostic / supporting grid runs：

| Run | Guard | Bases | Templates | Combinations | Attenuation positive rate | Note |
|---|---|---:|---:|---:|---:|---|
| dynaguard_pku2k | DynaGuard | 2000 | 2 | 15 | 1.000 | current-grid support, not 3-template spotlight row |
| qwen3guard_beavertails200 | Qwen3Guard | 200 | 2 | 15 | 0.000 | current-grid support, not 3-template spotlight row |
| qwen3guard_beavertails500 | Qwen3Guard | 500 | 2 | 15 | 0.667 | current-grid support, not 3-template spotlight row |
| qwen3guard_pku200 | Qwen3Guard | 200 | 2 | 15 | 0.000 | current-grid support, not 3-template spotlight row |
| wildguard_pku2k | WildGuard | 2000 | 2 | 15 | 0.000 | current-grid support, not 3-template spotlight row |
| harmaug_beavertails200_3neutral | HarmAug | 200 | 3 | 20 | 1.000 | diagnostic 3-template run, not counted as formal E3 guard |

解释：E3 完成 spotlight 设计覆盖目标，但效应方向必须 guard-specific。DynaGuard positive attenuation 强；Qwen3Guard / WildGuard 的 attenuation 行为不能被写成“全部 guard 都鲁棒”。报告应强调 3-template coverage closed，而不是 all-effect uniformity。

## 8. E6 / P0-5：Probability / Logit Robustness

### 8.1 原设计

NeurIPS E6 和 AAAI P0-5 要求：

- 不只看 hard-label threshold crossing。
- 至少 2 个 score/logit/probability guards。
- 至少一个覆盖 PKU200 + external dataset。
- 报告 score drift、calibration、ECE / Brier、threshold dependence。

### 8.2 实际结果

证据：

```text
outputs/e6_score_level_analysis_20260603/e6_score_level_summary.json
outputs/e6_score_level_analysis_20260603/e6_score_level_summary.md
outputs/e6_score_level_analysis_20260603/e6_score_level_role_metrics.csv
outputs/e6_score_level_analysis_20260603/e6_score_level_paired_drift.csv
```

状态：

```text
completed_two_score_guard_families_with_external
```

Score-level drift table：

| Dataset | Guard | Bases | Attack drift | 95% CI low | 95% CI high | Drift p | Attack error gap |
|---|---|---:|---:|---:|---:|---:|---:|
| PKU200 | Qwen3Guard | 200 | 0.037479 | 0.030665 | 0.044674 | 0.000100 | 0.028750 |
| BeaverTails200 | Qwen3Guard | 200 | 0.047620 | 0.039338 | 0.055518 | 0.000100 | 0.049375 |
| BeaverTails500 | Qwen3Guard | 500 | 0.046558 | 0.042457 | 0.050996 | 0.000100 | 0.046667 |
| PKU200 | HarmAug | 200 | 0.012454 | 0.007790 | 0.017462 | 0.000100 | 0.008438 |
| BeaverTails200 | HarmAug | 200 | 0.012593 | 0.006389 | 0.019355 | 0.000100 | 0.008750 |

Legacy threshold sweep summary:

- HarmAug and Qwen3Guard probability/logit threshold sweeps available.
- Thresholds: 0.05, 0.10, ..., 0.95.
- Supported hard-label gap thresholds at p <= 0.05: HarmAug = 3, Qwen3Guard = 38 across available Qwen3Guard PKU200 / BeaverTails500 sweeps.

解释：E6 完成 two score/probability guard families with external 的要求。Qwen3Guard 与 HarmAug 的 pressure drift 都在 score/probability 层面可见，但该结果仍是 score/logit diagnostic，不是所有 guard family 的 threshold robustness certification。

## 9. E7：Power Curve and Sample-size Sensitivity

### 9.1 原设计

NeurIPS E7 要求：

- 以 base case 为 independent unit。
- 通过 subsampling / bootstrap 估计 raw gap、residual、attenuation 的 detection probability。
- 至少覆盖 DynaGuard / WildGuard / Qwen3Guard 三个 baselines。

### 9.2 实际结果

证据：

```text
outputs/mnsla_power_curve_dynaguard_pku2k_cf_mean_v1_20260601/mnsla_power_curve_summary.json
outputs/mnsla_power_curve_wildguard_pku2k_cf_mean_v1_20260601/mnsla_power_curve_summary.json
outputs/mnsla_power_curve_qwen3guard_beavertails500_20260603/mnsla_power_curve_summary.json
```

最终状态：

```text
completed_three_baseline_power_curves
```

Selected power-curve rows：

| Baseline | n_bases | raw support probability | residual support probability | attenuation support probability | Note |
|---|---:|---:|---:|---:|---|
| DynaGuard-PKU2K-cf_mean_v1 | 25 | 0.934 | 0.000 | 0.920 | early raw/attenuation detectable |
| DynaGuard-PKU2K-cf_mean_v1 | 50 | 1.000 | 0.048 | 1.000 | strong at 50 bases |
| DynaGuard-PKU2K-cf_mean_v1 | 200 | 1.000 | 0.862 | 1.000 | residual detectable as N grows |
| DynaGuard-PKU2K-cf_mean_v1 | 2000 | 1.000 | 1.000 | 1.000 | full-scale stable |
| WildGuard-PKU2K-cf_mean_v1 | 25 | 0.040 | 0.000 | 0.022 | small-effect low-N sensitivity |
| WildGuard-PKU2K-cf_mean_v1 | 100 | 0.852 | 0.016 | 0.790 | raw/attenuation become detectable |
| WildGuard-PKU2K-cf_mean_v1 | 200 | 0.996 | 0.148 | 0.996 | stable raw/attenuation |
| WildGuard-PKU2K-cf_mean_v1 | 2000 | 1.000 | 1.000 | 1.000 | full-scale residual also detectable |
| Qwen3Guard-BeaverTails500 | 25 | 0.242 | 0.000 | 0.000 | raw-only curve; no residual ledger |
| Qwen3Guard-BeaverTails500 | 50 | 0.888 | 0.000 | 0.000 | raw support improves |
| Qwen3Guard-BeaverTails500 | 100 | 1.000 | 0.000 | 0.000 | raw support stable |
| Qwen3Guard-BeaverTails500 | 500 | 1.000 | 0.000 | 0.000 | raw-only full external curve |

解释：E7 支持 scale-aware claim。Qwen3Guard 曲线是 raw-only，因为没有 separate residual prediction ledger，因此不能用它声称 residual/attenuation power。

## 10. E8 / P1-3：Slice Denominator + Uncertainty Audit

### 10.1 原设计

NeurIPS E8 和 AAAI P1-3 要求：

- 所有 slice 报告 denominator、CI、Holm correction。
- n_bases < 10 的 slice 不画色，只标 low-N。
- main text 只展示 high-support slice。

### 10.2 实际结果

证据：

```text
outputs/mn_sla_roadmap_completion_audit_20260602/e8_slice_denominator_uncertainty_audit.csv
outputs/mn_sla_roadmap_completion_audit_20260602/e8_slice_denominator_uncertainty_audit.md
outputs/hard_v3_slice_inference_20260501/slice_inference.csv
```

结果：

| 项目 | 数值 |
|---|---:|
| audited slice rows | 168 |
| low-N rows | 0 |
| global-Holm supported positive rows | 0 |
| status | `completed_existing_slice_audit` |

解释：E8 完成 denominator + uncertainty audit。该实验是 localization diagnostic，不是 mechanism proof。

## 11. E9 / P1-2：Release / Reproducibility Package

### 11.1 原设计

NeurIPS E9 和 AAAI P1-2 要求：

- 公开 aggregate-only package。
- 提供 hash manifest。
- 提供 release scanner report。
- deny-by-default release policy。
- controlled-access statement。
- 不公开 raw prompt、private key、annotation packet raw text、model weights/cache、unreviewed JSONL。

### 11.2 实际结果

证据：

```text
outputs/mn_sla_public_aggregate_package_20260602
outputs/mn_sla_public_aggregate_package_20260602/hash_manifest.csv
outputs/mn_sla_public_aggregate_package_20260602/release_scan_report.md
outputs/mn_sla_completion_and_release_audit_20260602/release_policy_manifest.csv
outputs/mn_sla_completion_and_release_audit_20260602/release_check.md
```

Release policy：

| Path pattern | Decision | Reason |
|---|---|---|
| `**/*` | deny_by_default | 只有明确 allowlist 的 aggregate artifact 可发布 |
| `artifacts/**/*` | allow_aggregate | curated public aggregate mirror |
| `outputs/**/*.jsonl` | deny_unless_separately_allowlisted | 可能包含 raw text 或 raw model output |
| `outputs/**/*SENSITIVE*` | deny | local-only sensitive artifacts |
| `outputs/**/private_answer_key*` | deny | private annotation answer keys |
| `data/**/*` | deny | source data may contain raw benchmark text |
| `models/**/*`, `.hf_cache/**/*` | deny | model weights/cache 不进入 release |

结果：

```text
E9 = completed_public_aggregate_package
```

解释：E9 完成 reproducibility / auditability 要求，但 release 只覆盖 aggregate artifacts，不覆盖 raw prompt inspection。

## 12. P0-6：Scale-aware Gate Variant and Claim Matrix

### 12.1 设计

AAAI P0-6 要求形成 scale-aware gate 和 allowed/disallowed claim matrix，避免把某一尺度上的诊断结果过度外推。

### 12.2 实际结果

证据：

```text
outputs/mn_sla_required_experiments_20260601/mn_sla_required_experiments_summary.md
outputs/mn_sla_required_experiments_20260601/mn_sla_required_experiments_summary.json
outputs/mn_sla_completion_and_release_audit_20260602/audit.md
```

Claim scope matrix：

| Evidence pattern | Allowed claim | Disallowed claim |
|---|---|---|
| PKU200/PKU2K raw gap supported, residual still detectable at scale | strong attenuation with detectable residuals | residual eliminated or certified invariant |
| Non-PKU HarmBench/XSTest source-pair raw gap/attenuation observed | external source-pair diagnostic replication | broad source-general robustness |
| Projection ablations favor same-base matched controls | matched-control necessity plus estimator/template diagnostic | deployable mitigation or SOTA superiority |
| HarmAug and Qwen3Guard probability/logit sweeps | two-guard probability/logit diagnostic | threshold robustness across all guard families |
| Human IAA passed | local blinded human validation | universal neutral-control validity or deployable defense |

## 13. AAAI P1-4：Multi-cultural / Language Pressure Cue Pilot

AAAI plan 中 P1-4 设计为 optional pilot：

| Variant | n | Purpose |
|---|---:|---|
| English variant | 50 | alternative authority/flattery wording |
| Chinese pilot | 50 | culturally adapted pressure cues |

当前工作区未发现该 optional pilot 的正式完成产物；它没有被纳入 NeurIPS E1-E9 spotlight completion audit。建议在论文中不要写成已完成。若后续面向 AAAI / societal-impact 强化，可单独补做，但当前 `ALL_COMPLETE` 不依赖 P1-4。

## 14. 最终主文表建议

### Main Table 1：Roadmap Completion

| Group | Status | Evidence |
|---|---|---|
| NeurIPS main-track minimum | completed | `milestone_a = completed` |
| Spotlight recommended package | completed | `milestone_b = completed` |
| Overall | ALL_COMPLETE | `roadmap_completion_audit.json` |

### Main Table 2：Human IAA

| Packet | Items | Cells | Annotators | Label IAA | Difficulty within-1 | Cue binary IAA | Fail-closed |
|---|---:|---:|---:|---:|---:|---:|---|
| Expanded blinded packet | 270 | 90 | 2 | 1.000 | 1.000 | 1.000 | passed |

### Main Table 3：Baseline Breadth

| Baseline | Status | Main claim role |
|---|---|---|
| DynaGuard | evaluated | formal aggregate diagnostic |
| WildGuard | evaluated | formal aggregate diagnostic |
| Qwen3Guard | evaluated_score_logit | score/logit formal-compatible baseline |
| HarmAug | evaluated_score_probability | score/probability formal-compatible baseline |
| BingoGuard | evaluated | formal aggregate diagnostic |
| ShieldLM | supplementary_only | supplementary breadth |

### Main Table 4：Score-level Drift

Use E6 table in Section 8.2.

### Main Figure 1：Protocol

Show clean / matched neutral / pressure attack arms at base-case unit, with same-base matched neutral as the key estimand.

### Main Figure 2：Wrong-conclusion Matrix

Use E4 result to show naive comparator inflation and verdict mismatch.

### Main Figure 3：Power Curves

Use E7 DynaGuard / WildGuard / Qwen3Guard curves.

## 15. Final Writing Boundary

可以写：

> The completed MN-SLA evidence package closes the planned main-track and spotlight-oriented experiments under aggregate-only release constraints: expanded blinded IAA, five main-compatible guard baselines, three-template estimator robustness, external source diagnostics, score-level drift analysis, power curves, slice uncertainty audit, and a public aggregate package.

不能写：

> MN-SLA solves social-pressure robustness.

不能写：

> All guard families are certified robust.

不能写：

> Matched-neutral controls universally eliminate residual pressure effects.

应写：

> Effect direction and strength remain guard-specific; the evidence supports a human-validated audit protocol and a spotlight-level aggregate experimental package, not a deployable defense.
