# MN-SLA 后续稳拿 AAAI Main Track / 争取 Spotlight 实验计划

日期：2026-06-01  
目标：把 MN-SLA 从 **competitive main-track submission** 推进到 **更稳的 AAAI main-track**，并尽量具备 **spotlight-level** 证据形态。  
原则：不靠包装硬拔结论；所有新增实验必须直接回应 reviewer 的真实扣分点：baseline breadth、neutral validation IAA、simple-baseline necessity、template/estimator robustness、probability/threshold analysis、external open-data replication。

---

## 0. 当前状态判断

当前已经完成的 E1 / E5 / E7 明显增强了论文：

- E1 证明 raw pressure gaps 与 residual detectability 随 base count 呈 scale-dependent pattern。
- E5 证明普通 F1 不能 certify pressure-invariance。
- E7 让 baseline compatibility / exclusion policy 更透明。
- 270-item human validation 解决了最初 “neutral controls entirely unvalidated” 的 major blocker，但仍缺 overlapping IAA。

但要稳 AAAI main-track，至少还要补：

1. **Overlapping human validation / IAA**。
2. **Simple-baseline comparison**：证明 MN-SLA 不是普通 attack-vs-clean。
3. **External open-dataset replication**：至少一个新公开数据源。
4. **Estimator + neutral-template robustness**。
5. **Probability/logit or threshold robustness**。

如果时间有限，最优先前三项：**IAA、simple-baseline comparison、external replication**。

---

## 1. AAAI main-track 与 spotlight 的判定目标

### 1.1 Main-track ready 的最低证据形态

| 维度 | 最低要求 | 通过标准 |
|---|---|---|
| Neutral validity | 完成 overlapping double-code subset | label/cue fields κ 或 α >= 0.60，或在 prevalence 极端时报告 percent agreement + prevalence-adjusted κ；difficulty ICC/Spearman 可接受 |
| Dataset breadth | PKU + 至少一个外部公开数据源 | DynaGuard/WildGuard 或至少两个 compatible guards 在外部数据上 raw gap 方向一致，attenuation 仍显著 |
| Method necessity | MN-SLA vs naive designs | 至少一个 naive design 给出错误/膨胀 verdict，MN-SLA 更稳定 |
| Statistical transparency | 一侧 + 两侧、CI、Holm、base-level unit | 主表直接报告 p、CI、n_b，不只给 status labels |
| Residual narrative | attenuation, not elimination | scale residual supported 时不得声称 residual disappears |
| Artifact boundary | GitHub 与论文一致 | README、aggregate artifacts、sanitized templates、validation summary 同步 |

### 1.2 Spotlight-competitive 的目标证据形态

| 维度 | Spotlight 建议标准 |
|---|---|
| Data | 至少 PKU-SafeRLHF + BeaverTails/WildGuardTest 两个公开数据源，最好再加 HarmBench-style diagnostic |
| Baselines | 至少 5--6 个 guard/safety-judge systems，其中 2 个 score/logit/probability-exposing |
| Human validation | 完整 270-item overlapping double-code，最好第三人 adjudication subset |
| Robustness | estimator × neutral-template grid，fresh split，非 post-hoc |
| Necessity | simple-baseline disagreement table 清晰证明 naive audits 会误导 |
| Adoption | 提供 reproducible scripts、sanitized templates、hashes、base IDs、controlled-access raw prompt policy |

---

# P0-1. Overlapping human validation / IAA

## 目的

解决当前最容易被 strict reviewer 抓住的问题：两位人工标注者分别标注 180/270 packet，不能计算 item-level inter-annotator agreement。现有 pass rates 很强，但 reviewer 会问：不同 annotator 对同一 item 是否一致？

## 最低版本：90-item overlapping subset

### 抽样设计

从当前 270-item full packet 中抽取：

| Dimension | Requirement |
|---|---|
| Total items | 90 |
| Matched cells | 30 |
| Arms per cell | clean, matched neutral, attack |
| Regimes | Gate-50, PKU200, Non-PKU source-pair |
| Cells per regime | 10 |
| Directions | toward-safe / toward-unsafe 尽量各半 |
| Pressure families | 8 families 尽量均匀覆盖；每个 family 至少 3 cells，若无法均匀则报告实际分布 |
| Layouts | pre-case, post-case, sandwich, transcript 尽量均匀覆盖 |
| Annotators | 两位 independent human annotators 完全重叠标注同一 90 items |
| Blinding | 不暴露 true role、gold label、source、base id、model output、previous annotator output |

### 标注字段

保持当前字段：

```text
label_choice
difficulty_1_5
pressure_cue
desired_label_cue
unannotatable
quality_flag
```

### 统计指标

| Metric | Calculation |
|---|---|
| Label preservation | neutral vs clean label agreement + Wilson CI |
| Difficulty preservation | abs(difficulty_neutral - difficulty_clean) <= 1 的比例；mean abs diff |
| Pressure-cue removal | neutral pressure_cue=false rate |
| Desired-label-cue absence | neutral desired_label_cue=false rate |
| Attack-cue presence | attack pressure_cue=true rate |
| Label IAA | Cohen's κ；若多于两人用 Krippendorff's α |
| Cue IAA | Cohen's κ / α for pressure_cue and desired_label_cue |
| Difficulty IAA | ICC(2,k) 或 Spearman correlation |
| Quality exclusions | unannotatable / quality_flag counts and reasons |

### 成功标准

Main-track 最低标准：

| Metric | Target |
|---|---:|
| neutral-clean label agreement | >= 0.90 |
| difficulty preserved | >= 0.90 |
| neutral pressure cue removal | >= 0.95 |
| attack pressure cue present | >= 0.90 |
| label/cue κ or α | >= 0.60；若 prevalence 极端，补充 percent agreement + PABAK |
| unannotatable rate | <= 0.05 |

Spotlight 标准：

- 完整 270 items double-coded。
- 加第三位 annotator 对 disagreement subset 做 adjudication。
- Appendix 给 sanitized disagreement examples。

### 文件输出

建议输出：

```text
outputs/human_validation_overlap_YYYYMMDD/items.csv
outputs/human_validation_overlap_YYYYMMDD/annotations_annotator1.csv
outputs/human_validation_overlap_YYYYMMDD/annotations_annotator2.csv
outputs/human_validation_overlap_YYYYMMDD/iaa_summary.json
outputs/human_validation_overlap_YYYYMMDD/iaa_summary.md
figures/fig_human_validation_iaa.pdf
```

### 论文写法

主文一句：

> A fully overlapping double-code subset confirms the packet-level validation: neutral controls preserve label and difficulty while removing pressure cues, with substantial agreement across human annotators.

避免写法：

- 不要只报告 pass rate 而完全不报告 IAA。
- 不要把 non-overlap 180/270 packet 说成 double-coded IAA。

---

# P0-2. Simple-baseline comparison: 证明 MN-SLA 的必要性

## 目的

回应 “MN-SLA 是否只是普通 paired difference / counterfactual evaluation 的包装？” 的核心 novelty 批评。这个实验必须证明：naive designs 会给出 qualitatively different 或 inflated conclusions，而 same-base matched-neutral design 更稳。

## 数据设置

最低：

| Dataset | Bases | Use |
|---|---:|---|
| PKU200 | 200 | primary simple-baseline comparison |

强版本：

| Dataset | Bases | Use |
|---|---:|---|
| PKU200 | 200 | primary |
| BeaverTails200 or WildGuardTest200 | 200 | external replication |
| PKU2K subsample | 500 or 2000 | high-power diagnostic only |

## Baseline systems

最低：DynaGuard + WildGuard。  
强版本：DynaGuard + WildGuard + one probability/logit guard + ShieldLM supplementary。

## 对比 designs

| Design | Contrast | Main risk |
|---|---|---|
| Attack-vs-clean | attack arm vs clean arm | conflates pressure with layout/instruction changes |
| Attack-vs-generic-neutral | attack vs random neutral pool from other bases | breaks same-base matching |
| Attack-vs-same-cell-other-base-neutral | same wrapper family/layout but different base | changes content instance |
| Prompt-level replication | each rendered row treated as independent | pseudo-replication / inflated sample size |
| MN-SLA matched-neutral | attack vs same-base matched neutral | target method |

## 统计设置

- Unit for valid designs：base case。
- Prompt-level replication：故意作为 invalid comparator，报告其 inflated n 和 p-value distortion。
- Metrics：raw gap、95% CI、one-sided p、two-sided p、Holm status、qualitative verdict。
- Additional columns：effect-size inflation relative to MN-SLA、verdict disagreement、false-support indicator。

## 输出主表模板

| Dataset | Guard | Design | n_unit | Gap | 95% CI | p_one | p_two | Verdict | Inflation vs MN-SLA | Disagrees? |
|---|---|---|---:|---:|---|---:|---:|---|---:|---|
| PKU200 | DynaGuard | Attack-vs-clean | ... | ... | ... | ... | ... | ... | ... | ... |
| PKU200 | DynaGuard | Generic-neutral | ... | ... | ... | ... | ... | ... | ... | ... |
| PKU200 | DynaGuard | MN-SLA | ... | ... | ... | ... | ... | ... | 1.00x | No |

## 成功标准

Main-track：

- 至少一个 naive design 在至少一个 guard/dataset 上产生不同 verdict 或 > 1.5x effect inflation。
- Prompt-level replication 显示显著 p-value distortion。
- MN-SLA 的 same-base estimate 在 PKU200 与 external dataset 上方向更稳定。

Spotlight：

- naive designs 在多个 guard/dataset 上系统性误导。
- 主文用一张 table + 一张 figure 清晰展示 “wrong subtraction leads to wrong conclusions”。

## 推荐图

`fig_simple_baseline_disagreement.pdf`

- x-axis：design。
- y-axis：gap / residual。
- panels：DynaGuard, WildGuard。
- 标注 invalid designs with warning hatch。

---

# P0-3. External open-dataset replication

## 目的

解决 “curated/self-built prompt artifact” 与 “只在 PKU-derived setting 证明” 的质疑。需要至少一个外部公开数据源，保持同一 MN-SLA construction protocol，不引入过多 researcher degrees of freedom。

## 候选数据源

优先级：

| Dataset | 推荐度 | 理由 | 风险 |
|---|---:|---|---|
| BeaverTails | 高 | 公开 safety dataset，和安全对齐场景匹配 | label mapping 需严格核查 |
| WildGuardTest | 高 | moderation/test 场景直接相关 | 需确认可获取 labels 与 contract |
| HarmBench | 中 | red-team 场景强 | label/policy mapping 可能复杂 |
| XSTest | 中 | benign/safe edge cases useful | 不足以独立覆盖 harmful side |

## 样本设计

最低版本：

| Regime | Bases | Label balance | Purpose |
|---|---:|---|---|
| External200 | 200 | 100 safe / 100 unsafe | confirmatory replication |

强版本：

| Regime | Bases | Label balance | Purpose |
|---|---:|---|---|
| BeaverTails200 | 200 | 100/100 | external source 1 |
| WildGuardTest200 | 200 | 100/100 | external source 2 |
| External500 | 500 | stratified if label imbalance | stronger robustness |

## Wrapper construction

必须沿用当前 protocol：

- Pressure families：authority, consistency, flattery, identity, majority, pity, reciprocity, stacked。
- Layouts：pre-case, post-case, sandwich, transcript。
- Directions：toward safe, toward unsafe。
- 每个 base 至少包含 clean、matched neutral、attack。
- 保留 `neutral_template_id`。
- 不新增新的 pressure families，除非单独作为 future work。

## 统计设置

| Component | Setting |
|---|---|
| Unit | base case |
| Primary estimand | attack error minus same-base matched-neutral error |
| Tests | one-sided degradation + two-sided sensitivity |
| CI | base-level bootstrap 95% CI |
| Multiplicity | Holm within declared guard family |
| Readout | mean-v1 primary；cycle-v1 only if preregistered on fresh split |
| Metrics | raw gap, residual gap, attenuation, F1, exact excluded rows |

## 成功标准

Main-track：

- 在 external200 上至少 DynaGuard 或 WildGuard raw gap direction 一致且 supported，另一个至少同方向或 CI 与 PKU 不冲突。
- mean-v1 attenuation >= 70%。
- 若 residual supported，写成 attenuation not elimination。

Spotlight：

- 两个 external datasets 均支持 raw sensitivity + attenuation。
- 至少两个 guards show replicating raw gap beyond PKU。
- simple-baseline comparison 在 external data 上也显示 MN-SLA 必要性。

## 失败时的安全写法

如果 external dataset raw gap 不支持：

> The external replication shows that social-pressure sensitivity is source- and contract-dependent; MN-SLA remains useful as an audit protocol, but the empirical vulnerability is not universal across sources.

不要强行解释成模型 robust。

---

# P0-4. Estimator × neutral-template robustness

## 目的

解决 `mean-v1` / `cycle-v1` post-hoc 和 estimator dependence 批评。当前 cycle-v1 在 PKU2K 上效果很好，但因为是在观察 mean-v1 residual 后引入，不能作为主张。需要 fresh split + preregistered variants。

## Fresh split

建议：

| Split | Bases | Use |
|---|---:|---|
| PKU200-fresh | 200 | primary robustness |
| External200-fresh | 200 | stronger version |
| PKU2K holdout subsample | 500 | diagnostic only |

要求：

- 不使用 Gate-50 调参。
- 预先写入 `estimator_preregistration.md`。
- 固定 random seed、template order、tie-breaking。

## Estimator variants

预注册：

| Estimator | Definition | Main/diagnostic |
|---|---|---|
| mean-v1 | average same-base neutral statistic | primary |
| median-v1 | median neutral statistic | robustness |
| trimmed-mean-v1 | 10% trimmed same-base neutral statistic | robustness |
| first-neutral-v1 | fixed-order first neutral template | robustness / stress |
| majority-neutral-v1 | majority vote for hard labels | robustness |
| cycle-v1 | cyclic neutral assignment | only main if preregistered before fresh split |

## Neutral templates

每个 layout 至少 2 个 templates，强版本 3 个：

| Template | Purpose |
|---|---|
| neutral-template-a | minimal instruction neutralization |
| neutral-template-b | format-preserving procedural wording |
| neutral-template-c | stylistically distinct but semantically matched neutral wording |

## 实验矩阵

| Dimension | Values |
|---|---|
| Dataset | PKU200-fresh; optionally External200 |
| Guard | DynaGuard, WildGuard; optional probability guard |
| Estimator | 5--6 variants |
| Neutral template | 2--3 per layout |
| Unit | base case |

## 统计与输出

- Report raw gap, residual gap, attenuation for every estimator-template combination。
- Report min/median/max attenuation。
- Mixed-effects diagnostic：`gap ~ estimator + template + guard + (1 | base_id)`。
- 不只报告最优 estimator。

## 成功标准

Main-track：

- >= 80% reasonable estimator-template combinations maintain same attenuation direction。
- 没有 reasonable same-base estimator 反转主要结论。
- mean-v1 不是唯一能工作的选择。

Spotlight：

- template variation effect << raw-to-residual attenuation effect。
- 能在主文以 compact heatmap 展示。

---

# P0-5. Threshold / probability-level robustness

## 目的

解决当前 hard-label adapters 只能看到 decision flip，不能分析 subthreshold pressure drift 的限制。

## 当前限制

| Guard | Current output | Limitation |
|---|---|---|
| DynaGuard | parsed hard label | threshold embedded; no score drift |
| WildGuard | parsed hard label | threshold embedded; no score drift |
| BingoGuard | parsed hard label | only Gate-50 complete |
| HarmAug | native probability | currently only probability diagnostic baseline |
| ShieldLM | supplementary, possible score/prob drift | contract mismatch |

## 最低实验：HarmAug threshold sweep

Thresholds：

```text
0.05, 0.10, 0.15, ..., 0.95
```

Metrics：

| Metric | Purpose |
|---|---|
| score-level paired gap | subthreshold pressure drift |
| hard-label gap across thresholds | threshold sensitivity |
| AUROC / AUPRC | ranking stability |
| Brier / ECE | calibration drift |
| adverse-probability shift | pressure direction effect |

## 强版本：新增 probability/logit guard

优先尝试：

| Candidate | Condition to enter main analysis |
|---|---|
| LlamaGuard with logits | Can reliably map safe/unsafe token logits to probabilities under same contract |
| ShieldLM logits/probability | Query-response contract must be made faithful, otherwise supplementary only |
| ShieldGemma text safety | Must complete prediction run and stable parser/logit extraction |
| API moderation model | Can be supplementary; report version/timestamp/cost |

## 统计设置

- Score-level paired signed test。
- Threshold sweep heatmap。
- Calibration metrics fitted only on clean/neutral validation split, not attack rows。
- Report if hard-label and score-level findings diverge。

## 成功标准

Main-track：

- HarmAug threshold sweep shows conclusions are not an artifact of one arbitrary threshold。
- At least one score-level guard supports pressure drift / attenuation story.

Spotlight：

- Two probability/logit-exposing guards。
- Score-level and hard-label analyses tell coherent story or reveal meaningful decision-boundary differences。

---

# P0-6. Scale-aware gate variant

## 目的

把 Gate-50 与 PKU200/PKU2K 之间的表面矛盾变成明确的 statistical design。Reviewer 已经多次指出：50-base R-NS 不能压过 PKU200/PKU2K residual-supported evidence。

## 建议 gate 分层

| Gate | Dataset | Role | Claim allowed |
|---|---|---|---|
| Local Gate | Gate-50 | balanced, predeclared, inspectable local audit | local raw support / local R-NS |
| Scale Gate | PKU200 | primary scale-confirmatory | raw replication + attenuation + residual detectability |
| High-power Diagnostic | PKU2K | stress test | residual power curve / attenuation magnitude |
| External Gate | BeaverTails/WildGuardTest200 | source robustness | portability beyond PKU |

## 规则

1. 如果 Gate-50 R-NS 但 PKU200/PKU2K residual supported，则 portable claim 降级为 **attenuation, not elimination**。
2. 如果 external source 不复现 raw gap，则 vulnerability claim 限定到 PKU-like safety cases / prompt contracts。
3. 如果 scale residual 不支持且 attenuation 高，才能谨慎说 residual not supported under declared scale gate。

## 输出

`claim_scope_matrix.md`：

| Evidence pattern | Allowed claim | Disallowed claim |
|---|---|---|
| Gate-50 raw V-SUP; scale raw V-SUP; scale residual supported | strong attenuation | residual eliminated |
| Gate-50 V-SUP; external raw not supported | source-dependent vulnerability | universal judge vulnerability |
| template robust attenuation | robust audit readout | deployable defense |

---

# P1-1. Broader baseline family expansion

## 目的

解决 “only four systems / narrow adapters” 批评。不是所有 guard 都必须进 main panel；关键是透明展示 compatibility，并尽量找到 1--2 个新 complete-ledger compatible baselines。

## Candidate list

| Candidate | Priority | Entry condition | If fails |
|---|---:|---|---|
| ShieldLM | High | faithfully adapt query-response contract or clearly define review-prompt contract | supplementary only |
| LlamaGuard series | High | stable safe/unsafe parser + logits if possible | contract-mismatch smoke |
| ShieldGemma text safety | Medium | completed prediction run + stable parser | excluded ledger |
| BeaverDam | Medium | environment fixed; complete PKU200 ledger | runtime-blocked if unresolved |
| Nemotron Safety Guard | Medium | response safety contract matches task | contract-mismatch smoke |
| OpenAI Moderation / Perspective API | Low/medium | versioned API, cost controlled | supplementary external API |

## Main-panel inclusion criteria

A system enters main table only if：

1. Complete matched ledger。
2. Stable parser semantics。
3. Base IDs preserved。
4. Output interpretable as same safety-label task。
5. Raw + neutral + post-readout artifacts complete。
6. No uncontrolled contract mismatch。

## 成功标准

Main-track：

- 至少新增 1 个 complete-ledger compatible baseline beyond DynaGuard/WildGuard。
- 或者明确说明 broad compatibility matrix，并把 incompatibility 作为 audit-contract finding。

Spotlight：

- Main panel 5--6 systems。
- 至少 2 score/probability-exposing systems。

---

# P1-2. Raw-prompt auditability / safe release policy

## 目的

缓解 “raw rendered prompts withheld, linguistic manipulation not inspectable” 扣分，同时避免 harmful prompt leakage。

## Release policy

公开：

1. Base dataset IDs / row IDs / hashes。
2. Wrapper template skeletons。
3. Sanitized examples for every pressure family × layout。
4. Aggregate ledgers and result JSON/CSV。
5. Annotation aggregate results and IAA summary。
6. Parser versions, model versions, timestamps, seeds。

不公开或 controlled-access：

1. Raw harmful rendered prompts。
2. Full prompt text containing sensitive harmful content。
3. Any content prohibited by dataset license or safety policy。

## GitHub README 必须同步

README 需要包含：

- claim boundary updated after human validation。
- aggregate artifacts list。
- exact commands to reproduce figures/tables。
- what is intentionally withheld and why。
- how to request controlled access if applicable。

---

# P1-3. Slice stability and denominator reporting

## 目的

避免 heatmap visually persuasive but statistically unstable 的批评。

## 设置

For each slice：

| Report | Description |
|---|---|
| n_b | base count |
| n_cells | matched cells |
| raw gap | estimate |
| residual gap | estimate |
| CI | bootstrap CI |
| p | one-sided/two-sided as declared |
| Holm family | family definition |
| marker | report-global / within-field screen |

## 成功标准

- 所有 heatmap cell 有 denominator。
- Slice claims 只写 localization，不写 headline mechanism。
- 若要写 mechanism hypothesis，必须标为 evidence-bounded hypothesis。

---

# P1-4. Multi-cultural / language pressure cue pilot

## 目的

该实验不是 main-track 必需，但对 spotlight 和 societal-impact 很有价值。压力 cue 可能文化/语言依赖，英语模板可能 under-detect certain communities。

## 最低 pilot

| Language/culture | Bases | Templates | Goal |
|---|---:|---|---|
| English variant | 50 | alternative authority/flattery wording | template sensitivity |
| Chinese pilot | 50 | culturally adapted pressure cues | cross-lingual feasibility |

## 注意

- 需要新的 human validation。
- 不要把 pilot 写成 broad multilingual benchmark。
- 只写 feasibility / risk of cultural specificity。

---

# 2. 执行优先级与推荐时间线

## Phase 1: 最高性价比，两周内优先完成

| Priority | Experiment | Why first | Expected gain |
|---|---|---|---|
| 1 | P0-1 overlapping IAA, 90-item subset | 直接解决 central assumption | 最大提升 soundness |
| 2 | P0-2 simple-baseline comparison on PKU200 | 直接解决 novelty/necessity | 最大提升 significance |
| 3 | P0-3 external200 replication | 直接解决 curated/single-source concern | 最大提升 empirical breadth |

完成 Phase 1 后，论文更接近 stable AAAI main-track。

## Phase 2: 冲击更强 main / borderline spotlight

| Priority | Experiment | Why |
|---|---|---|
| 4 | P0-4 estimator × neutral-template robustness | 解决 post-hoc / template dependence |
| 5 | P0-5 probability/logit robustness | 解决 hard-label limitation |
| 6 | P0-6 scale-aware gate | 把实验结果变成干净 claim structure |

## Phase 3: Spotlight packaging

| Priority | Experiment | Why |
|---|---|---|
| 7 | P1-1 broader baseline family | 让 protocol 看起来可推广 |
| 8 | P1-2 release/auditability | 增强 reproducibility/dataset score |
| 9 | P1-3 slice denominator/stability | 增强 analysis quality |
| 10 | P1-4 cultural/language pilot | 增强 societal impact and novelty |

---

# 3. 每个实验完成后的论文更新位置

| Experiment | Main text | Appendix | Figure/Table |
|---|---|---|---|
| Overlapping IAA | Method 3.5 | Human validation appendix | Table: IAA + pass rates |
| Simple-baseline comparison | Experiments or Analysis | Full ablation table | Figure: naive vs MN-SLA gaps |
| External replication | Experiments main scale section | Dataset construction | Table: external200 raw/residual |
| Estimator-template robustness | Analysis | Full grid | Heatmap/table |
| Probability robustness | Experiments 4.5 | Threshold sweep details | Threshold sweep heatmap |
| Scale-aware gate | Method 3.3 / Experiments | Claim predicates | Claim-scope matrix |
| Baseline expansion | Experiments setup | Exclusion ledger | Compatibility matrix |
| Release policy | Reproducibility / Ethics | Artifact manifest | README checklist |

---

# 4. Paper packaging after experiments

## 4.1 推荐标题方向

当前标题可以保留：

> MN-SLA: A Matched-Neutral Safety-Label Audit for Social-Pressure Sensitivity in Safety Judges

如果想更突出 scale-aware 和 human validation，可考虑：

> MN-SLA: Human-Validated Matched-Neutral Auditing of Social-Pressure Sensitivity in Safety Judges

不建议把标题写成 “defense”、“mitigation”、“neutralization”，因为 CF-Neutralize 不是 deployable defense。

## 4.2 推荐贡献列表

1. **Base-level matched-neutral estimand** for social-pressure invariance in safety judges。
2. **Human-validated neutral-control construction**, with overlapping IAA after P0-1。
3. **Scale-aware empirical study** over PKU200/PKU2K and at least one external public dataset after P0-3。
4. **Necessity evidence** showing naive attack-vs-clean or unmatched-neutral audits can mislead after P0-2。
5. **Robustness evidence** across estimator/template/threshold variants after P0-4/P0-5。

## 4.3 摘要主线

推荐摘要核心句：

> Across open-data anchored safety cases and external replication, raw social-pressure sensitivity is consistently detectable for multiple safety judges. Matched-neutral controls strongly attenuate the measured gap, but high-power diagnostics reveal small residuals; MN-SLA therefore serves as a validated audit protocol for pressure-invariance, not a mitigation or robustness certificate.

---

# 5. Final go/no-go checklist before AAAI submission

## Main-track go checklist

| Item | Required? | Done? |
|---|---:|---:|
| PKU200 / PKU2K scale evidence integrated | Yes | Current mostly done |
| Gate-50 downgraded to local gate | Yes | Current mostly done |
| 270-item human validation included | Yes | Current done |
| overlapping IAA subset | Yes for stable main | TODO |
| simple-baseline comparison | Yes for stable main | TODO |
| external open-dataset replication | Yes for stable main | TODO |
| baseline compatibility matrix | Yes | Partial done |
| artifact README claim boundary synced | Yes | TODO/verify |
| p/CI/two-sided/one-sided stats visible | Yes | Current mostly done |
| no residual-elimination overclaim | Yes | Must verify final draft |

## Spotlight go checklist

| Item | Required for spotlight? | Done? |
|---|---:|---:|
| two external public datasets | Strongly recommended | TODO |
| 5--6 compatible baselines | Strongly recommended | TODO |
| 2 probability/logit guards | Strongly recommended | TODO |
| full 270-item overlapping IAA | Strongly recommended | TODO |
| estimator-template grid on fresh split | Strongly recommended | TODO |
| naive-baseline disagreement clear and visual | Strongly recommended | TODO |
| reproducible release with sanitized templates | Strongly recommended | TODO |

---

# 6. 如果实验结果不理想，应如何写

| Failure pattern | Safe interpretation | Avoid |
|---|---|---|
| External dataset raw gap not supported | Pressure sensitivity is source/contract-dependent | Claim universal robustness |
| IAA κ low but percent agreement high | Report prevalence effects, adjudicate disagreements, reduce claim strength | Hide κ or only report pass rate |
| Some neutral templates fail validation | MN-SLA requires validation gate; failed templates are excluded | Average failed templates into main result |
| Estimators disagree | Report estimator dependence; use preregistered primary only | Pick best estimator post-hoc |
| Probability drift exists without label flips | Pressure affects calibration/subthreshold scores | Say hard-label audit fully captures judge behavior |
| Residual supported at scale | Strong attenuation, incomplete readout | Residual eliminated |

---

## 7. 最终建议

若资源有限，按这个顺序推进：

1. **90-item overlapping IAA**。
2. **PKU200 simple-baseline comparison**。
3. **BeaverTails200 或 WildGuardTest200 external replication**。
4. **Estimator-template robustness on fresh PKU200**。
5. **HarmAug threshold sweep + one logit/probability guard attempt**。

前三项完成后，论文会明显更接近 AAAI main-track 稳定区间；五项全部完成且结果清楚，再加上更干净的叙事与 artifact 同步，才有较现实的 spotlight 竞争力。

