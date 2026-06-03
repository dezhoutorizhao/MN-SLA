# MN-SLA: 数据来源、baseline 核查、证据强度与补充实验计划

日期：2026-06-01  
目标：把 MN-SLA 从“较强但仍有硬伤的 audit-protocol 稿件”提升到更稳的 ACL/EMNLP main-track 水平，并争取 spotlight。

---

## 1. 当前数据到底是开源数据集还是自建数据集？

### 1.1 严格结论

当前 MN-SLA 不是纯开源数据集，也不是完全自建数据集，而是：

> **开源安全数据集锚定的自建 matched-neutral audit artifact。**

其中：

| 组件 | 性质 | 当前状态 | 对审稿人的说法 |
|---|---|---|---|
| PKU-SafeRLHF base cases | 开源/公开学术数据集 | Gate-50、PKU200、PKU2K 的主要来源 | 应强调为 open-data anchored base cases |
| MN-SLA pressure wrappers | 作者自建 | 社会压力 cue、layout、direction、family 等 | 应强调为 authored audit transformations |
| MN-SLA matched-neutral controls | 作者自建 | 同 base、同 layout/format、去 pressure cue | 必须配合 human validation 才可信 |
| Human validation packets | 作者自建标注包 | 180-item 与 270-item 两套人工标注结果 | 应作为 neutral-control validity evidence |
| Non-PKU source-pair regime | 作者自建/混合来源 audit artifact | 用于 coverage / portability，不应用于源泛化强结论 | 应作为 coverage diagnostic，而非核心 benchmark |
| Public GitHub artifact | 公开代码 + aggregate artifacts | 不公开 raw rendered prompts | 应说明伦理/安全原因，并提供 hashes/base IDs/sanitized examples |

### 1.2 为什么审稿人更信服“开源数据集”？

审稿人担心的是：如果 base cases、pressure wrappers、neutral controls 都由作者构造，论文容易被视为 curated case study。把 PKU-SafeRLHF 作为主要 base source 有助于降低这个风险，因为它是公开的大规模安全对齐数据集。正式稿里应写成：

> We instantiate MN-SLA on public PKU-SafeRLHF-derived base cases, and author only the pressure/neutral wrappers required by the audit contrast.

但不能写成：

> MN-SLA uses a fully public benchmark.

因为 pressure wrappers、matched neutral controls、validation packets 仍然是作者构造的 audit artifact。

### 1.3 关键措辞建议

推荐主文用语：

> Our base safety cases are anchored in public safety-alignment data, primarily PKU-SafeRLHF. MN-SLA adds an authored matched-neutral audit layer: pressure wrappers and neutral controls are generated under a frozen construction protocol and validated by blinded human annotation. Thus, the empirical substrate is open-data anchored, while the matched-control artifact is newly constructed and released as aggregate audit artifacts.

不要用：

> We introduce a new benchmark dataset.

除非你愿意公开更完整的 raw prompts / base IDs / wrapper templates，否则这个说法会引发数据集复用性和审查性扣分。

---

## 2. 当前 baseline 对比对象与发表信息

### 2.1 主实验 baseline

| Baseline | 当前论文角色 | 输出形式 | 已核查发表信息 | 是否适合继续作为主 baseline |
|---|---|---|---|---|
| DynaGuard | Main attenuation / raw V-SUP | parsed hard label | ICLR 2026 Poster, *DynaGuard: A Dynamic Guardian Model With User-Defined Policies* | 适合。动态 policy-conditioned guard，和 MN-SLA 的 pressure sensitivity 很相关 |
| WildGuard | Main attenuation / raw V-SUP | parsed hard label | NeurIPS 2024 Datasets & Benchmarks Track, *WildGuard: Open One-stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs* | 适合。公开安全 moderation 工具，强 baseline |
| BingoGuard | Main guardrail / raw V-NS | parsed hard label | ICLR 2025 Poster, *BingoGuard: LLM Content Moderation Tools with Risk Levels* | 适合。风险等级 moderation，与 binary label audit 互补 |
| HarmAug | Main guardrail + probability diagnostic | native probability | ICLR 2025 Poster, *HarmAug: Effective Data Augmentation for Knowledge Distillation of Safety Guard Models* | 适合。提供 native probability，是 score-level diagnostic 的关键 |

### 2.2 Supplementary / excluded systems

| System | 当前论文角色 | 发表信息 | 风险与建议 |
|---|---|---|---|
| ShieldLM | Supplementary only | Findings of EMNLP 2024, *ShieldLM: Empowering LLMs as Aligned, Customizable and Explainable Safety Detectors* | 如果 adapter 能解决 query--response contract mismatch，可提升 baseline breadth；否则保留 supplementary |
| BeaverDam / R2 / ShieldGemma | Excluded | 不建议作为主表强行纳入 | 若缺 complete ledger / contract compatibility，强行纳入会伤 soundness |

### 2.3 建议新增 baseline

为了稳 main-track，建议至少新增 **1 个 probability/logit-exposing guard**。优先级：

1. **ShieldLM**：已有 EMNLP Findings 2024 发表，安全 detector 定位清楚；若能统一 query-response format，可从 supplementary 升为 main/supporting。
2. **LlamaGuard / LlamaGuard 2/3/4**：工业界常用 open guard，但需要核查具体版本、license、输出 logits 是否可用。
3. **ShieldGemma**：公开文本安全 moderation 模型，但要避免与图像版 ShieldGemma 2 混淆；若采用，必须明确版本。
4. **Aegis / OpenAI Moderation API / Perspective API**：可作为 external API / non-open supplementary，但不应替代开源主实验。

---

## 3. 当前证据强度能否达到 A 会 main track / spotlight？

### 3.1 当前 V12 证据的强项

1. **已从 50-base 叙事改为 scale-aware evidence stack**。这比旧版更科学，因为 reviewer 明确指出 50-base 太小，PKU200/PKU2K 才是更有说服力的 broad evidence。
2. **使用 PKU200 与 PKU2K 支持 raw gap replication + strong attenuation**。这是目前最有力的 empirical story。
3. **human validation 已补上**。270-item / 90-cell packet 的 label preservation、neutral-clean agreement、difficulty preservation、pressure cue removal 指标很强。
4. **主张边界更稳**：不再说 residual elimination，而说 attenuation with detectable residuals。
5. **matched-base ablation 已证明 arbitrary neutral substitution 不够**，这对 novelty 很重要。

### 3.2 当前 V12 仍然被扣分的硬点

| 风险 | 严重程度 | 为什么会扣分 |
|---|---:|---|
| 开源数据使用不够突出 | 高 | 如果看起来像全自建 prompt benchmark，reviewer 会怀疑 curated case study |
| human validation 无 overlapping IAA | 高 | 两位标注者分别标 180/270 packet，无法报告 item-level agreement |
| baseline 覆盖仍偏窄 | 高 | 主表 4 个系统，且 3 个是 hard-label parsed adapters |
| probability-level analysis 只有 HarmAug | 中高 | 无法判断 subthreshold pressure drift |
| estimator / neutral-template robustness 不足 | 高 | mean-v1 / cycle-v1 容易被看作 post-hoc |
| raw prompts 不公开 | 中 | 有安全理由，但会降低 linguistic manipulation 的可审查性 |
| CF-Neutralize 仍有包装过强风险 | 中 | 容易被误读成 mitigation 或 causal removal |

### 3.3 客观评分

在不新增实验、只靠 V12 包装的情况下：

| 目标 | 当前可达程度 | 判断 |
|---|---:|---|
| Findings | 较稳 | 约 3.5--4.0 |
| Main track | 有机会但不稳 | 约 3.5--3.8；遇到严格 reviewer 仍可能 2.5--3 |
| Spotlight | 不够 | 需要额外强证据，尤其 cross-dataset + IAA + robustness |

如果补充下面 P0 实验中的至少 3 项，并把论文叙事压缩得更清楚：

| 目标 | 预计可达程度 | 判断 |
|---|---:|---|
| Main track | 明显更稳 | 约 4.0 左右 |
| Spotlight | 有竞争力但不保证 | 取决于 cross-dataset 结果是否清楚、baseline breadth 是否明显扩大 |

---

## 4. 必须补充的实验与详细设置

下面按优先级排序。P0 是“稳 main-track”建议必做；P1 是“争取 spotlight”建议做。

---

# P0-1. 开源数据集上的 confirmatory replication

## 目的

把论文从“自建 prompt artifact 上的 protocol demonstration”提升为“公开安全数据集锚定的 audit study”。

## 数据设置

### 主数据源

1. **PKU-SafeRLHF**：继续作为主数据源。
   - PKU200：作为 primary confirmatory scale gate。
   - PKU2K：作为 high-power diagnostic，不叫 full public dataset。

### 新增公开数据源

至少新增一个，最好两个：

1. **BeaverTails**：公开 safety alignment 数据集，可作为与 PKU 同源但不同 split / dataset family 的外部 replication。
2. **WildGuardTest**：与 WildGuard paper 配套的人类标注 moderation test set，适合 safety moderation 场景。
3. **HarmBench**：若 prompt policy 与 MN-SLA 标签能稳定对齐，可作为 red-team 风格外部集；否则放 supplementary。

## 样本规模

最低可接受：

| Regime | Bases | Label balance | 用途 |
|---|---:|---|---|
| PKU200 | 200 | 100 safe / 100 unsafe | primary confirmatory |
| BeaverTails200 或 WildGuardTest200 | 200 | 100 safe / 100 unsafe | external open-dataset replication |
| PKU2K | 2,000 | 按可用标签 stratified | high-power diagnostic |

更强版本：

| Regime | Bases | 用途 |
|---|---:|---|
| PKU500 | 500 | stronger primary gate |
| BeaverTails500 | 500 | external replication |
| WildGuardTest500 | 500 | moderation-specific replication |

## Wrapper 设置

保持当前 pressure family / layout / direction，不要新增太多，否则会被质疑 researcher degrees of freedom。

- Pressure families：authority, consistency, flattery, identity, majority, pity, reciprocity, stacked。
- Layouts：pre-case, post-case, sandwich, transcript。
- Directions：toward safe, toward unsafe。
- 每个 base 至少生成：clean、matched-neutral、attack。
- 每个 neutral 保留 neutral-template id。

## 统计设置

- Unit：base-level，不是 rendered prompt。
- Primary estimand：raw pressure gap = attack error minus matched-neutral error。
- Tests：one-sided sign-flip for degradation + two-sided sensitivity report。
- CI：base-level bootstrap 95% CI。
- Multiplicity：Holm correction within declared baseline family。
- Report：raw gap、mean-v1 residual、attenuation percent、two-sided p、F1 / non-degradation sanity check。

## 成功标准

稳 main-track 的最低标准：

1. DynaGuard / WildGuard 至少在 PKU200 和一个外部开源数据集上 raw gap 方向一致。
2. matched-neutral readout attenuation ≥ 70% 或 ≥ 80%，并报告 residual 可检测性。
3. 如果 residual 在 scale 上显著，结论继续写成 strong attenuation, not elimination。

Spotlight 更强标准：

1. 至少 2 个公开数据源 + 2 个 raw-vulnerable guards 上结论一致。
2. simple baselines 与 MN-SLA 的结论出现明确差异，证明 protocol necessity。

---

# P0-2. Overlapping human validation / IAA 实验

## 目的

解决当前最容易被 reviewer 抓住的点：两位标注者分别标 180/270 packet，不能计算 item-level inter-annotator agreement。

## 推荐设置

### 最低版本

- 从当前 270-item packet 中抽取 90 items，由两位 annotator 重叠标注。
- 覆盖：3 regimes × 10 cells × 3 arms = 90 items。
- 每个 pressure family 至少 5 个 matched cells；每个 layout 至少 5 个 matched cells；toward safe / toward unsafe 各半。

### 强版本

- 两位 annotator 完整重叠标注 270-item packet。
- 如条件允许，加第三位 annotator 标注 disagreement subset。

## 标注字段

保持当前字段：

- label_choice
- difficulty_1_5
- pressure_cue
- desired_label_cue
- unannotatable
- quality_flag

## 报告指标

必须报告：

| 指标 | 方法 |
|---|---|
| label preservation | neutral vs clean label agreement + Wilson CI |
| difficulty preservation | abs difficulty diff ≤ 1 的比例 + mean abs diff |
| pressure-cue removal | neutral pressure_cue false rate |
| desired-label cue absence | neutral desired_label_cue false rate |
| attack cue presence | attack pressure_cue true rate |
| IAA for categorical fields | Cohen's κ 或 Krippendorff's α |
| IAA for difficulty | ICC 或 Spearman 相关 |

## 成功标准

稳 main-track：

- label agreement ≥ 0.90。
- neutral pressure cue removal ≥ 0.95。
- difficulty preserved ≥ 0.90。
- κ ≥ 0.60 或者如 κ 受 prevalence 影响，补充 percent agreement + prevalence-adjusted κ。

Spotlight：

- 完整 270 items 重叠标注。
- κ/α 与 bootstrap CI 一起报告。
- disagreement examples 在 appendix 中给出 sanitized examples。

---

# P0-3. Simpler-baseline comparison: 证明 MN-SLA 不是普通 attack-vs-clean

## 目的

解决 novelty/significance 批评：MN-SLA 是否只是“paired difference + 包装”？

## 实验设计

在同一批 bases 上比较以下 designs：

| Design | 对比方式 | 预期问题 |
|---|---|---|
| Attack vs Clean | attack arm vs clean arm | 混入 layout/instruction change |
| Attack vs Generic Neutral | attack vs unrelated neutral pool | 破坏 same-base matching |
| Attack vs Same-cell Other-base Neutral | wrapper family 相同但 base 不同 | 改变内容实例 |
| Prompt-level replication | 把每个 rendered prompt 当独立样本 | pseudo-replication |
| MN-SLA matched neutral | attack vs same-base matched neutral | 目标方法 |

## 样本规模

- 最低：PKU200。
- 更强：PKU200 + BeaverTails/WildGuardTest200。

## 输出表

主文应放一张 compact table：

| Method | Raw gap | Residual / adjusted gap | p | CI | Qualitative verdict | Disagrees with MN-SLA? |
|---|---:|---:|---:|---|---|---|

再加一列：

- false support rate
- false attenuation rate
- effect-size inflation relative to MN-SLA

## 成功标准

1. Attack-vs-clean 或 generic-neutral 在至少一个 baseline 上给出不同 verdict 或明显膨胀 gap。
2. Same-base matched neutral 在跨数据源上更稳定。
3. 用这个实验支撑论文 novelty：MN-SLA 的贡献不是“减法”，而是“防止错误减法”。

---

# P0-4. Estimator 与 neutral-template robustness

## 目的

解决 mean-v1 / cycle-v1 被认为 post-hoc 或 estimator-dependent 的问题。

## 实验设置

### Estimator variants

预注册以下 estimator：

1. mean-v1
2. median-v1
3. trimmed-mean-v1, trim = 10%
4. first-neutral-v1, fixed seed / fixed ordering
5. majority-neutral-v1 for hard labels
6. cycle-v1 仅作为 exploratory 或在 fresh split 上 preregistered 后进入 main

### Neutral templates

每个 layout 至少 2 个 neutral templates，强版本 3 个：

- neutral-template-a：minimal instruction neutralization
- neutral-template-b：format-preserving procedural wording
- neutral-template-c：semantically equivalent but stylistically different neutral wording

## 数据

- Fresh PKU200 split，不能用已经调过的 Gate-50。
- 如果有时间，加 BeaverTails200 / WildGuardTest200。

## 统计

- 每个 estimator × template 组合报告 raw gap、residual、attenuation。
- Mixed effects model：gap ~ estimator + template + baseline + (1 | base_id)。
- 报告最大/最小/中位 attenuation，不只报最优。

## 成功标准

稳 main-track：

- ≥ 80% estimator-template combinations 保持同方向 attenuation。
- 没有一个 reasonable same-base estimator 反转结论。

Spotlight：

- neutral-template variation 对 attenuation 的影响小于 raw gap attenuation 主效应。
- 结果可以放入主文 Figure / Table，而不是仅 appendix。

---

# P0-5. Threshold / probability-level robustness

## 目的

解决当前 hard-label adapter 只能看到 decision flip，无法分析 subthreshold pressure drift 的问题。

## 当前限制

- DynaGuard / BingoGuard / WildGuard：当前 artifact 是 parsed hard labels。
- HarmAug：native probability，可用于 soft-score analysis。

## 推荐补充

### 最低版本

- 对 HarmAug 做完整 threshold sweep：threshold ∈ {0.1, 0.2, ..., 0.9}。
- 报告 score-level gap、hard-label gap、AUROC/AUPRC、calibration drift。

### 强版本

新增至少一个 probability/logit-exposing guard：

- ShieldLM 如果 logits 可访问；
- LlamaGuard 系列如果可从模型 logits 得到 safe/unsafe token probability；
- ShieldGemma 文本安全模型如能稳定导出 logits。

## 统计

- Score-level signed paired test。
- Threshold sweep heatmap。
- Calibration：ECE / Brier score；如果需要，temperature scaling 只在 clean/neutral validation split 上拟合，不允许在 attack rows 上调参。

## 成功标准

1. raw pressure sensitivity 不只是单一 threshold artifact。
2. attenuation 结论在 reasonable thresholds 下稳定。
3. 如果 hard-label 和 score-level 不一致，主文解释为 decision-boundary vs score-drift difference。

---

# P1-1. Broader baseline family 扩展

## 目的

解决 “only four systems” 的窄 baseline 批评。

## 建议 baseline 组

| 类别 | 推荐系统 | 理由 |
|---|---|---|
| Open moderation guard | WildGuard, BingoGuard, ShieldLM, LlamaGuard | 标准开源安全 judge |
| Dynamic policy guard | DynaGuard | 与自定义 policy pressure 场景相关 |
| Distilled / efficient guard | HarmAug | native probability + distilled guard |
| Industrial/API-style guard | OpenAI Moderation API / Perspective API | 可放 supplementary，不作开源主claim |

## 纳入条件

只有满足以下条件才进 main table：

1. 完整 matched ledger。
2. parser semantics stable。
3. base ids preserved。
4. 输出可解释为 same safety-label task。
5. raw + neutral + post-readout artifacts complete。

否则放 supplementary/excluded ledger，不强行纳入。

---

# P1-2. Raw prompt 可审查性增强

## 目的

解决 reproducibility 与 linguistic manipulation 不可审查的问题，同时不暴露敏感 harmful content。

## 建议 release policy

1. 公开 base dataset IDs / row IDs / hashes。
2. 公开 wrapper templates 的 sanitized skeletons。
3. 每个 pressure family + layout 至少给 1 个 sanitized running example。
4. raw rendered prompts 不公开，但提供 controlled-access packet 或 ethics-reviewed request process。
5. GitHub README 同步删除 “completed human validation not supported” 的过期边界。

## 主文表述

> We release code, aggregate artifacts, base identifiers, hashes, and sanitized wrapper templates. Raw rendered prompts are withheld from the public repository due to harmful-content and benchmark-leakage concerns, but the aggregate ledger and validation summaries make the claim boundary inspectable.

---

## 5. 论文是否能靠“包装”达到稳 main-track / spotlight？

### 5.1 客观结论

不能只靠包装。

当前论文已经可以通过包装减少 reviewer 的误解，例如：

- 弱化 50-base；
- 突出 PKU200 / PKU2K；
- 把 CF-Neutralize 降级为 diagnostic；
- 强调 open-data anchored base cases；
- 把 human validation 放到主文；
- 用 simple-baseline comparison 讲清楚 MN-SLA necessity。

这些可以把论文从 borderline Findings / borderline main 往 main-track 推。但如果没有新增至少几个实验证据，strict reviewer 仍会抓住：baseline 太少、IAA 不足、template robustness 不足、probability-level 不足。

### 5.2 最优包装路线

推荐标题方向：

> Scale-Aware Matched-Neutral Auditing of Social-Pressure Sensitivity in Safety Judges

摘要第一句不要写 “we propose a benchmark”。应写：

> We audit whether safety-label judges change decisions when the same public safety case is embedded in social-pressure wrappers, using matched neutral controls validated by human annotation.

贡献列表建议四条：

1. Matched-neutral base-level estimand。
2. Human-validated neutral-control construction。
3. Scale-aware open-data empirical study over PKU200 / PKU2K plus local Gate-50。
4. Ablations showing why simpler comparisons fail。

### 5.3 Main-track 稳妥版本需要做到

最低补强组合：

1. PKU200 改为 primary confirmatory gate。
2. 新增一个外部开源数据集 200-base replication。
3. 完成 overlapping human validation subset，报告 IAA。
4. 完成 simple-baseline comparison。

如果四项都完成，main-track 会明显更稳。

### 5.4 Spotlight 版本需要做到

Spotlight 需要更像“社区会采用的方法”，而不是“一个仔细的 case study”。建议目标：

1. 两个开源数据源：PKU-SafeRLHF + BeaverTails/WildGuardTest。
2. 至少 5--6 个 guard systems，其中至少 2 个 probability/logit-exposing。
3. 完整 IAA validation。
4. Neutral-template robustness。
5. Simple-baseline disagreement table，证明 MN-SLA 改变结论。
6. GitHub artifact 与主文 claim 完全同步。

达到这些后，可以包装成：

> the first human-validated, scale-aware matched-control audit protocol for social-pressure sensitivity in safety judges, with evidence that naive prompt-level audits can mislead.

这比“CF-Neutralize 让 residual 不显著”更有 spotlight 潜力。

---

## 6. 立即行动清单

### 今天即可修改论文的部分

1. Data paragraph 改成 “open-data anchored + authored audit layer”。
2. 摘要突出 PKU200 / PKU2K，不突出 Gate-50。
3. Gate-50 放 secondary/local gate。
4. Baseline table 加年份/venue。
5. GitHub README 与论文 claim 同步。
6. 删减重复 disclaimer，使论文更像 scientific paper，少像 rebuttal。

### 需要跑实验的部分

1. 新增 open-dataset replication：BeaverTails200 或 WildGuardTest200。
2. Overlapping human validation subset。
3. Simple-baseline comparison。
4. Estimator × neutral-template robustness。
5. Probability/logit baseline 扩展。

### 最建议优先完成的三个实验

若时间有限，只做这三个：

1. **Overlapping human validation subset**：最直接解决 central assumption。
2. **Open-dataset external replication**：最直接解决 curated/self-built concern。
3. **Simple-baseline comparison**：最直接解决 novelty/necessity concern。

