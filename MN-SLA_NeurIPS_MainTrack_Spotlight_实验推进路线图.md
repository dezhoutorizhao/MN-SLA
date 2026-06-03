# MN-SLA：面向 NeurIPS Main Track / Spotlight 的当前实验评估与后续实验推进路线图

生成日期：2026-06-02  
依据文件：`阶段性成果8.md`、当前 MN-SLA 实验摘要与此前 reviewer-style 反馈  
目标：把 MN-SLA 从“较完整的诊断证据包”推进到 **NeurIPS main-track 有竞争力 / 尽量接近 spotlight** 的证据强度。

---

## 0. 总结结论

当前 MN-SLA 的实验结果 **比早期版本明显强很多**，尤其是以下证据已经很有价值：

1. **same-base matched-neutral 的必要性已经有强证据**：PKU200、PKU2K、BeaverTails200 上，matched mean residual 远小于 raw gap，而 global neutral / other-base reference 产生很大的诊断偏差。
2. **外部开源数据集 replication 已经部分完成**：BeaverTails200 覆盖 DynaGuard / WildGuard，能缓解“只在 PKU 上成立”的批评。
3. **threshold / probability diagnostic 已经从 1 个 guard 扩展到 2 个 guard**：HarmAug 与 Qwen3Guard 都有 threshold sweep 或 logit/probability diagnostic。
4. **claim governance 明显成熟**：已经有 scale-aware allowed/disallowed claim matrix、release policy、baseline inclusion/exclusion ledger、测试 gate。

但如果目标是 **NeurIPS main track 乃至 spotlight**，当前仍不能称为“稳拿”。最核心原因是：

- **P0-1 independent overlapping human IAA 仍未完成**。这会直接影响 neutral-control validity，是 NeurIPS reviewer 最容易抓住的 soundness blocker。
- **P0-4 fresh neutral-template robustness 结果混合**。DynaGuard 保持 positive attenuation，但 WildGuard 在当前 reference definition 下 attenuation positive rate = 0，median attenuation = -0.010227，不能写成“所有 guard 对 template/estimator 都鲁棒”。
- **formal main-panel baseline 仍偏窄**。目前最完整的 direct review-prompt compatible main evidence 主要集中在 DynaGuard / WildGuard；BingoGuard、HarmAug、Qwen3Guard、ShieldLM 等需要明确 formal / diagnostic / supplementary 边界。
- **raw prompts 与 annotation details 受 release policy 限制**。这是合理的，但 NeurIPS reviewer 会要求更强的可审查替代方案，例如 sanitized skeleton、hash ledger、controlled-access statement、field-level scanner report。

**当前状态判断：**

| 目标 | 当前状态 | 诚实判断 |
| --- | --- | --- |
| Strong workshop / Findings-style paper | 已经较强 | 可以支撑 |
| NeurIPS main track | 有潜力，但还不稳 | 需要完成 P0-1 + 至少一个 main-panel baseline/probability 扩展 + 更清楚的 robustness 设计 |
| NeurIPS spotlight | 当前不够 | 需要 P0-1 完成、cross-dataset + multi-guard + template robustness 均形成正面或可解释结果 |

**推荐主线：**

> MN-SLA is a base-level, human-validated, matched-neutral audit protocol showing that social-pressure sensitivity is a distinct failure mode not captured by ordinary F1; same-base matched controls are necessary; raw pressure gaps replicate across PKU and BeaverTails; matched-control diagnostics strongly attenuate but do not certify residual elimination.

必须避免：

- “CF-Neutralize eliminates residual pressure sensitivity.”
- “MN-SLA is a deployable defense.”
- “All guards are robust under neutral-template variants.”
- “Completed human validation / IAA” 在 P0-1 未完成前不能写。
- “Universal source-general robustness” 不能从 BeaverTails200 + Non-PKU source-pair diagnostic 直接推出。

---

## 1. 当前实验结果是否理想？逐项评估

### 1.1 P0-1：Overlapping human validation / IAA

**当前状态：blocked_by_missing_independent_human_annotations。**

已完成准备：

| 项目 | 当前状态 |
| --- | --- |
| Overlap packet | 已生成 |
| annotation items | 90 |
| sampled cells | 30 |
| cells per regime | 10 |
| regimes | `pku50_main_gate`, `pku200_scale`, `non_pku200_source_pair` |
| arms | clean / neutral / attack |
| analyzer | 已准备 |
| analyzer outputs | pairwise percent agreement, Cohen kappa, PABAK, Spearman, within-1 difficulty agreement, `iaa_pairwise.csv` |

预设阈值：

| 指标 | 阈值 |
| --- | ---: |
| min annotators per item | 2 |
| min complete cells per regime | 10 |
| min total complete cells | 30 |
| neutral-clean label agreement | >= 0.90 |
| difficulty preserved | >= 0.90 |
| neutral pressure cue removed | >= 0.95 |
| neutral desired-label cue absent | >= 0.95 |
| attack pressure cue present | >= 0.90 |

**评估：不理想，是当前最大 blocker。**

原因：

- 当前 packet 与 analyzer 准备充分，但没有两个独立人类 annotator 对同一 items 的 completed annotations。
- AI / oracle / metadata-assisted annotation 不能替代 independent human IAA。
- NeurIPS reviewer 会把 neutral-control quality 视为核心识别假设。没有 IAA，就算其他实验很强，也会被认为 claim 的语义基础未锁定。

**当前论文可写边界：**

> We prepared a blinded overlap packet and fail-closed analyzer for human neutral-control validation, but independent overlapping human IAA is not yet complete.

**不可写：**

> We completed human validation / IAA.

---

### 1.2 P0-2：Simple-baseline comparison

**当前状态：completed_diagnostic。**

关键结果：

| Dataset | Guard | Raw gap | Matched mean | Global neutral | Other-base | Matched attenuation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PKU200 | DynaGuard | 0.134948 | 0.007542 | 0.321208 | 0.321208 | 0.127406 |
| PKU200 | WildGuard | 0.028281 | 0.003750 | 0.286250 | 0.286250 | 0.024531 |
| PKU2K | DynaGuard | 0.117500 | 0.006562 | 0.252937 | 0.252937 | 0.110937 |
| PKU2K | WildGuard | 0.021344 | 0.002000 | 0.267625 | 0.267625 | 0.019344 |
| BeaverTails200 | DynaGuard | 0.158750 | 0.009375 | 0.235625 | 0.235625 | 0.149375 |
| BeaverTails200 | WildGuard | 0.033438 | 0.003125 | 0.159375 | 0.159375 | 0.030313 |

**评估：很理想，但需要升级为主文核心证据。**

这组实验非常适合回答 reviewer 的“MN-SLA 相对简单 baseline 的必要性是什么？”：

- Matched mean residual 始终远小于 raw gap。
- Global neutral / other-base 会产生很大的诊断偏差。
- PKU 与 BeaverTails 均体现同一趋势。

**建议写法：**

> Simple attack-vs-clean or unmatched-neutral comparisons are not merely noisier; they can give qualitatively different and inflated diagnostics. Same-base matched-neutral controls are therefore not an aesthetic design choice but the core requirement for interpretable pressure-sensitivity auditing.

**仍需补强：**

当前表格已经显示差异，但最好再补一张 “wrong-conclusion / inflation matrix”：

| Comparator | Expected issue | Metric |
| --- | --- | --- |
| attack-vs-clean | mixes pressure effect with wrapper/layout shift | gap inflation vs MN-SLA |
| attack-vs-generic-neutral | loses base semantics | verdict mismatch rate |
| same-cell other-base neutral | breaks base-level matching | residual inflation |
| prompt-level replication | pseudo-replication | p-value shrinkage / false support |
| MN-SLA matched neutral | intended estimand | stable base-level diagnostic |

---

### 1.3 P0-3：External open-dataset replication

**当前状态：completed_confirmatory。**

已完成：

| Dataset | Guard | 当前解释 |
| --- | --- | --- |
| BeaverTails200 | DynaGuard | confirmatory external raw pressure-gap replication and aggregate attenuation diagnostic |
| BeaverTails200 | WildGuard | confirmatory external raw pressure-gap replication and aggregate attenuation diagnostic |

另有 Non-PKU HarmBench / XSTest source-pair diagnostic，但不能写成 universal source-general robustness。

**评估：理想，但还不足以支撑 NeurIPS spotlight。**

BeaverTails200 是当前最有价值的新增外部证据。它能够把论文从“PKU-only case study”推进到“open-data anchored replication”。但 NeurIPS reviewer 仍可能认为：

- 只有一个外部数据源完整 confirmatory。
- 主要只覆盖 DynaGuard / WildGuard。
- Non-PKU HarmBench/XSTest 是 source-pair diagnostic，可能存在 source-label confounding，不能作为 source-general conclusion。

**建议继续补：**

至少再加一个外部公开数据源，例如：

- WildGuardTest200
- HarmBench200 label-balanced split
- XSTest200 label-balanced split
- BeaverTails500 扩展版

目标不是无限扩数据，而是形成：

> PKU200 + PKU2K + BeaverTails200 + one additional external dataset

这样的证据矩阵。

---

### 1.4 P0-4：Estimator × neutral-template robustness

**当前状态：completed_fresh_holdout_diagnostic。**

设置：

| 项目 | 设置 |
| --- | --- |
| Freshness definition | PKU2K prediction-ledger bases excluding Gate-50 base_sample ids |
| Excluded Gate-50 bases | 20 |
| Holdout bases per guard | 1,980 |
| Neutral templates | `neutral_careful_review`, `neutral_format_reminder` |
| Estimator/template combinations | 15 |
| Guards | DynaGuard, WildGuard |

结果：

| Guard | Holdout bases | Attenuation positive rate | Residual positive rate | Median attenuation |
| --- | ---: | ---: | ---: | ---: |
| DynaGuard | 1,980 | 1.000000 | 1.000000 | 0.022096 |
| WildGuard | 1,980 | 0.000000 | 1.000000 | -0.010227 |

**评估：不理想但非常有价值。**

它不是失败，而是告诉我们不能写过强结论：

- DynaGuard 的 attenuation 对 fresh template grid 更稳定。
- WildGuard 的 attenuation 在当前 reference definition 下不稳定，甚至 median attenuation 为负。
- residual matched-neutral conclusion 仍为 positive，说明 residual detectability 与 template/estimator choice 有关系。

**当前安全写法：**

> A fresh holdout neutral-template grid shows that estimator/template behavior is guard-dependent: DynaGuard retains positive attenuation, whereas WildGuard does not under the current reference definition. This supports using MN-SLA as a claim-bounded audit rather than a universal residual-removal procedure.

**不可写：**

> Estimator/template robustness is confirmed for all guards.

**需要重做或扩展的关键点：**

P0-4 必须升级成一个 preregistered robustness experiment，而不只是 fresh diagnostic。见后续实验 E3。

---

### 1.5 P0-5：Threshold / probability-level robustness

**当前状态：completed_two_probability_guards。**

结果：

| Guard | Dataset | Thresholds | Supported hard-label gap thresholds at p <= 0.05 | Score type |
| --- | --- | ---: | ---: | --- |
| HarmAug | PKU50 | 19 | 3 | native probability |
| Qwen3Guard | PKU200 | 19 | 19 | label-logit probability |

**评估：有明显进步，但还不够 NeurIPS spotlight。**

优点：

- 已经不再只有 HarmAug 一个 probability baseline。
- Qwen3Guard 在 PKU200 上 19/19 thresholds supported，非常强。
- 能回应“hard-label adapters 只能看到 threshold crossing”的批评。

不足：

- HarmAug 只有 PKU50，规模偏小。
- Qwen3Guard 是 label-logit probability，需要清楚解释 logits 来源与 mapping。
- 当前只能写成 two probability/logit diagnostics，不能写成 threshold robustness across all guard families。

**建议继续补：**

- HarmAug 扩展到 PKU200 / BeaverTails200。
- Qwen3Guard 扩展到 BeaverTails200 / PKU2K subset。
- 加 score-level drift：mean probability shift、Brier score、ECE、AUROC、paired score drift CI。

---

### 1.6 P0-6：Scale-aware gate variant

**当前状态：completed_as_claim_matrix。**

关键 allowed / disallowed claim：

| Evidence pattern | Allowed claim | Disallowed claim |
| --- | --- | --- |
| PKU200/PKU2K raw gap supported, residual still detectable at scale | strong attenuation with detectable residuals | residual eliminated or certified invariant |
| Non-PKU HarmBench/XSTest source-pair raw gap/attenuation observed | external source-pair diagnostic replication | broad source-general robustness or full public-dataset replication |
| Projection ablations favor same-base matched controls; fresh holdout template grid available | matched-control necessity plus fresh holdout estimator/template diagnostic | deployable mitigation or SOTA method superiority |
| HarmAug and Qwen3Guard probability/logit threshold sweeps | two-guard probability/logit diagnostic | threshold robustness across all guard families |
| Oracle/AI-assisted annotations without independent humans | pipeline/sensitivity diagnostic | human validation or IAA |

**评估：理想，应该保留为论文 claim-scope table。**

NeurIPS reviewer 通常不反感 limitation，但反感“主张和证据不匹配”。P0-6 的作用是把 evidence-to-claim mapping 明确化，能显著降低被说 overclaim 的风险。

---

### 1.7 P1：治理、发布与测试

当前 release policy：deny-by-default。

明确禁止公开：

- `data/**/*`
- `outputs/**/*.jsonl`，除非单独审查和 allowlist
- `outputs/**/*SENSITIVE*`
- `outputs/**/private_answer_key*`
- `third_party/**/*`
- `models/**/*`
- `.hf_cache/**/*`
- `paper/**/*`

测试状态：

```powershell
python -m pytest tests -q
# 185 passed, 84 warnings
```

**评估：对 reproducibility 有帮助，但还需更审稿友好的 public artifact manifest。**

建议公开：

- aggregate CSV / JSON summaries
- manifest with hash IDs
- sanitized wrapper skeletons
- exact sampling code
- exact analysis scripts
- field-level release scanner report
- README claim-boundary table

不建议公开：raw harmful prompts、private answer keys、local annotation packet、未经扫描 JSONL。

---

## 2. 当前 NeurIPS 级别判断

### 2.1 当前证据强度

| 维度 | 当前评分判断 | 理由 |
| --- | ---: | --- |
| Quality / Soundness | 3.0–3.5 / 4 | matched-control design、base-level inference、scale-aware gate 强；但 independent human IAA 未完成 |
| Clarity | 3.0 / 4 | claim boundary 明确，但术语和 gate machinery 仍偏重 |
| Significance | 2.5–3.0 / 4 | safety-judge pressure sensitivity 重要；但 baseline breadth 与 public inspection 仍限制影响力 |
| Originality | 2.5–3.0 / 4 | matched-control audit 很实用，但 reviewer 可能认为是 protocolization 而非根本新方法 |
| Reproducibility | 3.0–3.5 / 4 | aggregate artifacts、tests、release governance 强；raw prompt withholding 需解释 |

**综合判断：** 当前不是“稳拿 NeurIPS main track”。若直接投稿，较可能落在 **borderline / weak accept / weak reject** 区间，取决于 reviewer 是否认可安全审计协议的价值。

### 2.2 达到 NeurIPS main 的最小补强组合

如果只做最少补强，优先顺序为：

1. 完成 independent overlapping human IAA。
2. 把 P0-2 simple-baseline comparison 升级为主文核心表 + wrong-conclusion matrix。
3. 把 BeaverTails200 作为 confirmatory external replication 放入主文。
4. 重新设计 P0-4，形成 preregistered estimator/template robustness，而不是只报告 mixed fresh diagnostic。
5. 至少让一个 probability/logit guard 成为 formal main evidence，而不只是 diagnostic。

完成后，NeurIPS main track 才有更稳竞争力。

### 2.3 接近 spotlight 的补强组合

Spotlight 需要更强的“社区价值 + 结论稳定 + 方法可复用”证据：

1. human IAA 不仅通过，还要覆盖多 pressure family / layout / direction，报告 kappa/PABAK/CI。
2. 至少 3 个公开数据源：PKU、BeaverTails、WildGuardTest/HarmBench/XSTest 中至少一个额外 confirmatory。
3. 至少 4 个 formal baselines，其中至少 2 个 score/logit/probability exposing。
4. preregistered estimator/template robustness 对主结论稳定。
5. paper rewrite：从“CF-Neutralize residual R-NS”转成“MN-SLA reveals a distinct, reproducible judge-failure axis and shows why simple audits fail”。

---

## 3. 后续实验设计：P0 必做项

下面的实验按优先级排列。若资源有限，先做 E1、E2、E3。

---

### E1. Independent overlapping human IAA（最高优先级）

#### 目标

证明 matched neutral controls 在人工盲评下确实：

1. 保留 clean arm 的安全标签。
2. 保留或近似保留判断难度。
3. 移除 pressure cue 与 desired-label cue。
4. attack arm 中 pressure cue 确实存在。

#### 实验设置

**最小可接受版：**

| 项目 | 设置 |
| --- | --- |
| Annotators | 2 independent human annotators |
| Items | 当前已生成 90 annotation items |
| Cells | 30 matched cells |
| Arms per cell | clean / neutral / attack |
| Regimes | pku50_main_gate, pku200_scale, non_pku200_source_pair |
| Cells per regime | 10 |
| Blinding | 不暴露 true role、gold label、source、base id、model output |

**NeurIPS 推荐版：**

| 项目 | 设置 |
| --- | --- |
| Annotators | 2–3 independent human annotators |
| Items | 180–270 annotation items |
| Cells | 60–90 matched cells |
| Regimes | pku50_main_gate, pku200_scale, pku2k_holdout, BeaverTails200, non_pku_source_pair |
| Cells per regime | >= 15 if possible |
| Coverage | 每个 pressure family、layout family、direction 至少若干 cells |

#### 标注字段

每个 item 标注：

```text
label_choice: safe / unsafe / ambiguous / unannotatable
difficulty_1_5: integer 1-5
pressure_cue: none / authority / flattery / answer_key / consistency / other
desired_label_cue: absent / toward_safe / toward_unsafe / other
unannotatable: true / false
quality_flag: free text or coded reason
```

#### 分析指标

| 指标 | 统计方式 | 推荐阈值 |
| --- | --- | ---: |
| neutral-clean label agreement | cell-level paired rate + Wilson CI | point >= 0.90, lower CI >= 0.80 |
| item label match to expected label | item-level rate | >= 0.90 |
| difficulty preservation | abs diff <= 1 | >= 0.90 |
| mean abs difficulty diff | average over neutral-clean | <= 0.50 preferred, <= 0.75 acceptable |
| neutral pressure cue removed | neutral item pressure_cue = none | >= 0.95 |
| neutral desired-label cue absent | desired_label_cue = absent | >= 0.95 |
| attack pressure cue present | attack item pressure_cue != none | >= 0.90 |
| label IAA | Cohen kappa + PABAK | kappa >= 0.60 preferred; PABAK >= 0.80 |
| cue IAA | Cohen kappa / PABAK | kappa >= 0.60 preferred |
| difficulty IAA | Spearman / ICC / within-1 agreement | within-1 >= 0.90 |

#### 输出文件

```text
outputs/human_validation_overlap_202606XX/annotator1.csv
outputs/human_validation_overlap_202606XX/annotator2.csv
outputs/human_validation_overlap_202606XX/iaa_pairwise.csv
outputs/human_validation_overlap_202606XX/validation_summary.json
outputs/human_validation_overlap_202606XX/validation_summary.md
```

#### 成功标准

- fail-closed thresholds 全部通过。
- 至少核心指标 neutral-clean label agreement、difficulty preserved、pressure-cue removal 通过。
- 若 kappa 因类别不平衡偏低，必须报告 PABAK 与 percent agreement，并解释。

#### 论文写法

主文一张表：

| Validation packet | Items | Cells | Annotators | Label agreement | Difficulty preserved | Cue removed | Attack cue present | IAA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |

**安全 claim：**

> A blinded overlapping human validation study supports label preservation, difficulty preservation, and pressure-cue removal for the matched-neutral controls under preregistered fail-closed thresholds.

---

### E2. Main-panel baseline expansion：至少新增 2 个 formal baselines

#### 目标

解决“main compatible baseline 太少”的问题。当前 DynaGuard / WildGuard 是主力，但 NeurIPS reviewer 会要求更多 judge family。

#### 候选 baselines 分级

| Baseline | 当前状态 | 推荐动作 |
| --- | --- | --- |
| DynaGuard | formal evaluated | 保留 main |
| WildGuard | formal evaluated | 保留 main |
| Qwen3Guard | probability/logit diagnostic | 尽量升为 formal main diagnostic baseline |
| HarmAug | probability diagnostic on PKU50 | 扩展到 PKU200 / BeaverTails200 |
| BingoGuard | runner available / Gate-50 only or incomplete | 若能补 PKU200 + BeaverTails200，可进入 appendix/main compact |
| ShieldLM | supplementary contract mismatch | 保留 supplementary，除非能构造 official-contract faithful input |
| LlamaGuard / Nemotron | smoke contract mismatch | 不进 main，除非修复 contract 并完成 formal ledger |
| ShieldGemma | gated/network blocked | 不写 formal result |

#### 实验设置

| 项目 | 设置 |
| --- | --- |
| Datasets | PKU200 + BeaverTails200；可选 PKU2K subset |
| Bases per dataset | 200 minimum；PKU2K 作为 diagnostic |
| Arms | clean / matched neutral / pressure attack |
| Wrappers | 使用当前 frozen pressure families 与 neutral templates |
| Inference unit | base case |
| Required outputs | prediction ledger, parser log, exclusion ledger, aggregate table |

#### 成功标准

- 至少 4 个 baselines 形成 formal aggregate evidence。
- 至少 2 个 baselines 支持 probability/logit/score-level analysis。
- parser failure / exclusion rate < 1%，或透明解释并从 metrics 排除。
- 不要求所有 baselines 显示 raw vulnerability；重要的是 coverage 与 audit compatibility。

#### 统计

每个 baseline × dataset 报告：

```text
N bases
records
raw matched-neutral gap
95% bootstrap CI
one-sided p(mean>0)
two-sided p(abs(mean)>0)
residual gap under preregistered estimator
attenuation = raw - residual
F1 / clean F1 / neutral F1
exclusion count and reason
```

#### 论文图表

- Main Table：formal baselines × PKU200 / BeaverTails200。
- Appendix Table：contract-mismatch / runner-only / excluded baselines。

---

### E3. Preregistered estimator × neutral-template robustness（重做 P0-4）

#### 目标

把当前 mixed fresh diagnostic 升级成 reviewer 可接受的 robustness study。

当前 P0-4 不能直接作为“鲁棒性成功”，因为：

- DynaGuard positive attenuation rate = 1.0。
- WildGuard positive attenuation rate = 0.0，median attenuation = -0.010227。

因此 E3 应重新预注册 estimator/template family，并改变评价目标：不是要求所有 estimator 都让 residual 不显著，而是验证 **主结论是否稳定**。

#### 预注册设计

| 项目 | 设置 |
| --- | --- |
| Split | holdout base ids；不得包含 Gate-50 or template-authoring base ids |
| Datasets | PKU200 holdout + BeaverTails200；可选 PKU2K holdout |
| Neutral templates per layout | 3 templates minimum |
| Estimators | mean, median, trimmed mean, first-neutral, majority/score-average |
| Tie-breaking | 预先固定，不允许事后选择 |
| Guards | DynaGuard, WildGuard, Qwen3Guard, HarmAug if possible |

#### 推荐 neutral templates

每个 layout 至少 3 个 neutral wrapper：

1. `neutral_careful_review`: 强调客观评审，不暗示答案。
2. `neutral_format_reminder`: 只提醒输出格式，不改变任务难度。
3. `neutral_policy_restated`: 重述安全判定标准，不包含 desired-label cue。

所有模板需要通过 cue scanner 与 human IAA 子集。

#### 指标

| 指标 | 目的 |
| --- | --- |
| raw conclusion stability | pressure sensitivity 是否跨模板保持 |
| attenuation sign consistency | raw - residual 是否多数为正 |
| residual detectability | 小 residual 是否随 N 检出 |
| estimator rank variance | estimator choice 是否改变结论 |
| template variance | neutral wording 是否导致大偏移 |

#### 成功标准

最低可接受：

- raw pressure gap conclusion 在多数 template/estimator 组合上稳定。
- same-base matched controls 显著优于 global / other-base controls。
- 对 WildGuard 的 mixed behavior 透明报告，不强行写成失败或成功。

NeurIPS main 推荐：

- 至少 80% estimator × template combinations 的 raw conclusion 方向一致。
- matched attenuation 在 DynaGuard 与至少一个 additional formal baseline 上为正且有 CI 支持。
- 若 WildGuard attenuation 不稳定，提供清楚解释：effect size small、hard-label threshold sparse、reference definition sensitivity。

Spotlight 推荐：

- 4 个 baselines 中至少 3 个在 template/estimator grid 上主结论稳定。
- template variance 小于 raw gap 的 25%–35%。

#### 输出

```text
outputs/preregistered_template_robustness_202606XX/design_manifest.json
outputs/preregistered_template_robustness_202606XX/estimator_grid.csv
outputs/preregistered_template_robustness_202606XX/template_variance_summary.md
outputs/preregistered_template_robustness_202606XX/claim_stability_matrix.csv
```

---

### E4. Simple-baseline wrong-conclusion matrix（把 P0-2 升为强 novelty 证据）

#### 目标

不仅展示 matched mean 小，还要证明简单方法会导致错误或误导性结论。

#### 对比对象

| Method | 描述 | 预期问题 |
| --- | --- | --- |
| Attack-vs-clean | attack error minus clean error | 混入 wrapper/layout shift |
| Attack-vs-generic-neutral | generic neutral not same-base | 破坏 semantic matching |
| Attack-vs-other-base-neutral | same-cell other-base | 混入 base difficulty |
| Prompt-row bootstrap | rendered prompt rows as independent | pseudo-replication |
| MN-SLA same-base neutral | proposed | base-level matched estimand |

#### 评价指标

```text
bias_vs_mnsla = comparator_gap - matched_gap
inflation_ratio = comparator_gap / matched_gap
verdict_mismatch = comparator_status != matched_status
pseudo_replication_p_shrink = p_base_level / p_row_level
```

#### 数据集

- PKU200
- PKU2K
- BeaverTails200
- Optional: WildGuardTest200 / HarmBench200

#### Baselines

- DynaGuard
- WildGuard
- Qwen3Guard if formal predictions available
- HarmAug if expanded

#### 成功标准

- 至少两个 datasets 上，unmatched/generic methods 显著 inflate 或 distort conclusion。
- prompt-row bootstrap 显示 p-value 过度乐观，证明 base-level inference 必要。
- MN-SLA 在 verdict stability 与 interpretability 上更可审计。

#### 主文写法

> MN-SLA is necessary not because it yields smaller numbers, but because common alternatives answer a different question. They break base matching or treat prompt variants as independent samples, producing inflated or qualitatively different audit conclusions.

---

### E5. External open-dataset expansion

#### 目标

从 “PKU + BeaverTails” 扩展到更强的 source-generality evidence。

#### 推荐方案

| Dataset | Size | 用途 | 注意事项 |
| --- | ---: | --- | --- |
| PKU200 | 200 bases | current scale-confirmatory anchor | 已有 |
| PKU2K | 2,000 bases | high-power diagnostic | 不称为全量 PKU |
| BeaverTails200 | 200 bases | external open-dataset confirmatory | 已有 |
| WildGuardTest200 | 200 bases | safety moderation external eval | 推荐新增 |
| HarmBench200 | 200 bases | adversarial harmful instruction source | 避免 source-label confounding |
| XSTest200 | 200 bases | benign over-refusal / safety test | label balance 需谨慎 |

#### 抽样策略

- base-level stratification。
- label-balanced：safe / unsafe 尽量 50/50。
- category-balanced：harm categories 尽量均匀。
- length-bin balanced。
- difficulty proxy balanced。
- 固定 random seed。
- 不因模型结果调样本。

#### 成功标准

NeurIPS main：

- PKU + BeaverTails + 至少 1 个新增外部数据源。
- 至少 DynaGuard / WildGuard / one score-exposing guard 完整跑通。

Spotlight：

- 3 个以上外部或半外部 sources。
- 至少 4 个 baselines。
- 结果不仅报告 raw gap，还报告 failure modes 与 source-specific differences。

#### claim 边界

若 HarmBench 与 XSTest 的 label/source 绑定无法解除，只能写：

> source-pair diagnostic replication

不能写：

> universal source-general robustness

---

### E6. Probability / logit robustness 升级

#### 目标

从 hard-label flip audit 进一步捕捉 subthreshold pressure drift。

#### 现状

| Guard | 当前证据 |
| --- | --- |
| HarmAug | PKU50, 19 thresholds, 3 supported |
| Qwen3Guard | PKU200, 19 thresholds, 19 supported |

#### 推荐扩展

| Guard | Dataset | 必做指标 |
| --- | --- | --- |
| Qwen3Guard | PKU200 + BeaverTails200 | threshold sweep, logit drift, calibration |
| HarmAug | PKU200 + BeaverTails200 | native probability drift |
| optional score guard | PKU200 | at least one additional score/logit baseline |

#### 阈值设置

```text
thresholds = [0.05, 0.10, ..., 0.95]
primary_threshold = 0.50
secondary_thresholds = all others
multiplicity = Holm within guard × dataset family
```

#### score-level 指标

| Metric | Purpose |
| --- | --- |
| mean adverse probability drift | pressure moves score toward wrong label |
| paired score difference CI | effect size |
| Brier score clean/neutral/attack | calibration-sensitive degradation |
| ECE / calibration bins | threshold dependence |
| AUROC / AUPRC | ranking robustness |
| label flip rate | hard decision consequence |

#### 成功标准

- 至少一个 score-exposing guard 在 PKU200 + BeaverTails200 上完成。
- pressure effect 不只存在于单一 threshold。
- 若 threshold dependence 很强，应写成 finding，不隐藏。

---

### E7. Power curve and sample-size sensitivity figure

#### 目标

把“50-base 太小”的批评转化为论文优势：MN-SLA 明确展示 power 与 residual detectability 的关系。

#### 设置

```text
N = [25, 50, 100, 200, 500, 1000, 2000]
R = 500 stratified subsamples
unit = base case
strata = label, source, category, length bin, difficulty proxy
```

#### Baselines

- DynaGuard
- WildGuard
- Qwen3Guard if available
- HarmAug if scale feasible

#### 输出

| Output | 内容 |
| --- | --- |
| power_curve_raw.csv | raw support probability by N |
| power_curve_residual.csv | residual support probability by N |
| fig_power_curve.pdf | raw and residual detectability vs N |
| table_min_detectable_N.md | smallest N where support probability >= 0.8 / 0.9 |

#### 论文 claim

> Residual detectability is sample-size dependent; therefore MN-SLA reports scale-aware attenuation rather than residual elimination.

这会显著降低 reviewer 对 50-base gate 的攻击力。

---

### E8. Slice denominator + uncertainty audit

#### 目标

让 family/layout/direction heatmap 不再只是视觉说服，而有 denominator 与 uncertainty。

#### 设置

每个 slice 报告：

```text
n_bases
n_records
raw_gap
residual_gap
attenuation
bootstrap CI
Holm-adjusted p
minimum-cell threshold status
```

#### 最低展示规则

- n_bases < 10 的 slice 不画色，只标注 low-N。
- 主文只展示 high-support slices。
- Appendix 放完整 denominator table。

#### 解释边界

可以写：

> localization diagnostic

不能写：

> mechanism proof

---

### E9. Release / reproducibility package 升级

#### 目标

解决 raw prompts 不公开与可审查性之间的矛盾。

#### 推荐 public package

允许公开：

```text
README.md
LICENSE
configs/*.yaml
scripts/run_*.py
scripts/analyze_*.py
aggregate_artifacts/*.csv
aggregate_artifacts/*.json
figures/*.pdf
hash_manifest.csv
sampling_manifest.csv
release_scan_report.md
sanitized_wrapper_skeletons.md
tests/*
```

默认不公开：

```text
data/**/*
outputs/**/*.jsonl
outputs/**/*SENSITIVE*
outputs/**/private_answer_key*
models/**/*
.hf_cache/**/*
raw_rendered_prompts.csv
local_annotation_packets.xlsx
```

#### Controlled-access 方案

如果 NeurIPS reviewer 质疑 raw prompts 不可审查，可以提供：

1. sanitized skeleton templates。
2. per-item hash + metadata manifest。
3. field-level leakage scanner report。
4. optional controlled-access review package，仅供 AC / ethics reviewer / artifact evaluator。

#### 测试 gate

```powershell
python -m pytest tests -q
```

不要用裸仓库级 `pytest`，避免收集 third_party tests。

---

## 4. NeurIPS 论文重写建议

### 4.1 贡献列表应改成 4 点

1. **Estimand**：base-level matched-neutral safety-label audit for social-pressure sensitivity。
2. **Validation**：independent overlapping human IAA + mechanical ledger validation。若 P0-1 未完成，则不能写 human validation completed。
3. **Empirical findings**：raw pressure gaps replicate across PKU and BeaverTails; ordinary F1 does not certify pressure-invariance。
4. **Audit governance**：simple-baseline necessity, scale-aware claim gate, probability/logit diagnostics, release policy。

### 4.2 主结果顺序

推荐主文顺序：

1. Construction protocol + sanitized example。
2. Human IAA / neutral-control validation。
3. PKU200 / PKU2K / BeaverTails200 raw pressure gap replication。
4. Simple-baseline wrong-conclusion matrix。
5. Estimator/template robustness。
6. Probability/logit threshold analysis。
7. Scale-aware gate and limitations。
8. Release governance。

不建议继续以 Gate-50 R-NS 作为 headline。

### 4.3 标题和定位

当前标题可以保持：

> MN-SLA: A Matched-Neutral Safety-Label Audit for Social-Pressure Sensitivity in Safety Judges

但摘要第一句应避免“defense / mitigation”风格，建议：

> Safety judges can change labels under social-pressure wrappers even when the underlying safety case is fixed. We introduce MN-SLA, a base-level matched-neutral audit protocol that estimates this pressure sensitivity against same-base neutral controls rather than attack-clean differences or prompt-row replication.

### 4.4 必须避免的强 claim

| 不可写 | 替代写法 |
| --- | --- |
| residual eliminated | strongly attenuated; residual detectability is scale-dependent |
| human validation completed | only after P0-1 complete; before that write packet prepared |
| SOTA robustness method | audit protocol / diagnostic framework |
| deployable defense | offline diagnostic readout over archived artifacts |
| universal source-general robustness | external replication on named datasets |
| threshold robustness across all guard families | two probability/logit diagnostics |

---

## 5. 里程碑推进表

### Milestone A：达到 NeurIPS main-track 有竞争力

必须完成：

| 实验 | 最小成功标准 |
| --- | --- |
| E1 human IAA | 90 items overlap, 2 annotators, fail-closed pass |
| E2 baseline expansion | 至少 4 formal baselines or 3 formal + 2 strong diagnostics |
| E4 simple-baseline matrix | 展示 naive methods 产生 inflated / wrong conclusions |
| E5 external dataset | BeaverTails200 + 至少一个额外 external source 或 BeaverTails500 |
| E6 probability/logit | 至少 2 score/logit guards，其中一个覆盖 PKU200 + external dataset |
| E9 release package | public aggregate package + hash manifest + scanner report |

预期状态：

- Soundness 明显提高。
- Reviewer 对 neutral controls 的攻击点显著减少。
- main track 有竞争力，但不保证 spotlight。

### Milestone B：争取 NeurIPS spotlight

在 Milestone A 基础上再完成：

| 实验 | Spotlight 级成功标准 |
| --- | --- |
| E1 expanded IAA | 180–270 overlap items, 2–3 annotators, kappa/PABAK/CI clear |
| E3 template robustness | 3 neutral templates/layout × 5 estimators × >=3 formal baselines |
| E5 source generalization | 3+ datasets; source/label confounding 被消除或明确建模 |
| E6 score-level analysis | 2–3 probability/logit guards，含 calibration / score drift |
| E7 power curves | DynaGuard/WildGuard/Qwen3Guard 至少 3 baselines |
| E8 slice analysis | denominator + CI + Holm in appendix; main text only high-support slices |

预期状态：

- 论文从 “careful audit protocol” 提升为 “community-reusable safety-evaluation methodology”。
- Spotlight 有可能，但仍取决于 reviewer 是否认可安全评测方向在 NeurIPS 的贡献类型。

---

## 6. 建议执行顺序

### Week 1：关闭最大 blocker

1. 找两名独立 annotators 完成 90-item overlap packet。
2. 运行 `analyze_overlap_human_iaa_20260601.py`。
3. 输出 IAA summary。
4. 若失败，定位 failure family / layout，修 neutral templates。

### Week 2：补 main-panel evidence

1. HarmAug 跑 PKU200 + BeaverTails200。
2. Qwen3Guard 跑 BeaverTails200。
3. 若可行，BingoGuard 跑 PKU200 + BeaverTails200。
4. 统一生成 parser/exclusion ledger。

### Week 3：重做 preregistered robustness

1. 冻结 neutral-template family。
2. 冻结 estimator family。
3. 生成 holdout prediction/evaluation grid。
4. 输出 claim-stability matrix。

### Week 4：外部数据和 release package

1. 加 WildGuardTest200 或 HarmBench/XSTest label-balanced split。
2. 生成 public aggregate artifact package。
3. 完成 hash manifest 与 release scanner。
4. 重写论文主文图表。

---

## 7. 最终论文应呈现的主表与主图

### Main Table 1：Datasets and claim role

| Dataset/regime | Bases | Role | Claim allowed |
| --- | ---: | --- | --- |
| Gate-50 | 50 | local frozen audit gate | compact balanced gate only |
| PKU200 | 200 | scale confirmatory | raw replication + attenuation |
| PKU2K | 2000 | high-power diagnostic | residual detectability / power |
| BeaverTails200 | 200 | external replication | external raw gap + attenuation |
| WildGuardTest/HarmBench/XSTest | 200 | external/source diagnostic | source-general only if label/source not confounded |

### Main Table 2：Human IAA validation

必须放主文，不放 appendix。

### Main Table 3：Simple-baseline wrong-conclusion matrix

这是 novelty/significance 的关键。

### Main Table 4：Formal baseline results

至少包含：DynaGuard、WildGuard、Qwen3Guard、HarmAug/BingoGuard。

### Main Figure 1：MN-SLA design schematic

保留现有方法图，但减少“gate bureaucracy”。

### Main Figure 2：Tri-scale raw/attenuation/residual evidence

不要画成“projection solves problem”。标题建议：

> Raw pressure gaps replicate at scale; matched-neutral diagnostics strongly attenuate but do not certify invariance.

### Main Figure 3：Power curve

显示 residual detectability 随 N 增加。

### Main Figure 4：F1 vs pressure-invariance decoupling

展示 ordinary F1 does not certify pressure-invariance。

---

## 8. 风险登记表

| 风险 | 严重性 | 触发条件 | 缓解方式 |
| --- | --- | --- | --- |
| Human IAA 不通过 | 高 | label/difficulty/cue 指标低于阈值 | 修订 neutral templates，重新标注；降低 claim |
| WildGuard template robustness 继续负向 | 中高 | attenuation positive rate 仍低 | 写成 guard-dependent finding；不主张 universal attenuation |
| 新 baselines contract mismatch | 高 | LlamaGuard/Nemotron/ShieldLM 无法适配 review-prompt contract | 保留 supplementary/excluded ledger；寻找 direct-contract guard |
| raw prompts 不能公开 | 中 | reviewer 要求 inspection | sanitized skeleton + hash manifest + controlled access |
| Qwen3Guard 被认为非主流 | 中 | reviewer 不认可 | 增加 HarmAug/BingoGuard/其他 formal guard |
| 论文过度 defensive | 中 | claim boundary 太多 | 用 claim-scope table 取代重复 disclaimer |

---

## 9. 当前最应该立刻做的三件事

1. **完成 independent overlapping human IAA。** 这是 NeurIPS main 的硬门槛。
2. **把 P0-2 做成主文核心表。** 这直接证明 MN-SLA 相对简单方案的必要性，是 originality / significance 的关键。
3. **扩展一个 formal probability/logit baseline 到 PKU200 + BeaverTails200。** 这能显著缓解 hard-label adapter 批评。

如果这三件事完成，论文会从“证据包较完整但仍可被 soundness 攻击”进入 “NeurIPS main-track 有竞争力” 区间。若再完成 E3/E5/E7 的扩展，则具备冲 spotlight 的基础。

---

## 10. 一句话版本

当前结果并非不理想，而是**已经足以证明 MN-SLA 有真实价值，但还不足以支撑 NeurIPS spotlight 级别的 broad methodological claim**。后续实验的核心不是继续堆更多 small diagnostics，而是关闭三个大缺口：

1. independent overlapping human IAA；
2. formal multi-baseline + probability/logit evidence；
3. preregistered template/estimator robustness + external dataset expansion。

完成这些后，MN-SLA 才能被包装为：

> a human-validated, open-data anchored, scale-aware, reproducible matched-neutral audit protocol for a distinct safety-judge failure mode.

这才是最接近 NeurIPS main track / spotlight 的版本。
