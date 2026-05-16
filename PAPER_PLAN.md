# PAPER PLAN: Counterfactual Social-Pressure Robustness for Safety Judges

Target venue: ICLR-style ML conference paper.

Main body target: 8-9 pages excluding references and appendix.

## Working Title

Counterfactual Social-Pressure Robustness for Safety Judges

## Paper Type

Empirical method-and-evaluation paper. The main contribution is a counterfactual matched-neutral evaluation contract plus a plug-in post-hoc/test-time neutralization layer evaluated on selected strong safety-judge baselines.

## Claims-Evidence Matrix

| Claim | Evidence | Status | Section |
| --- | --- | --- | --- |
| HARD V3 isolates pressure-specific degradation by comparing pressure attacks to matched neutral controls under fixed base content. | HARD V3 protocol; 50-base core balanced split; zero missing neutral controls; 1600 primary attacks per run. | Supported | Section 3 |
| Strong safety judges can exhibit supported social-pressure gaps under HARD V3. | DynaGuard raw PASS with primary gap 0.163750; WildGuard raw PASS with primary gap 0.040625. | Supported | Section 4 |
| The plug-in counterfactual neutralization layer removes supported gaps on raw-PASS baselines. | DynaGuard method residual gate FAIL; WildGuard method residual gate FAIL; paired attenuation positive with Holm-adjusted p-values. | Supported | Section 4 |
| The layer does not introduce supported gaps on raw-FAIL baselines and preserves utility. | BingoGuard and HarmAug remain gate FAIL after wrapping; all selected method pairs preserve or improve overall and attack F1. | Supported | Section 4 |
| The result is limited to a matched-neutral post-hoc/test-time contract and is not equal-cost, single-pass, or deployable-model SOTA. | Cost/contract boundary; extra or cached neutral controls; auto-review READY for exact limited claim only. | Supported limitation | Section 5 |

## Section Plan

### Abstract

- Problem: safety judges may follow social pressure rather than content evidence.
- Approach: HARD V3 matched-neutral evaluation and a plug-in counterfactual neutralization layer.
- Key result: DynaGuard and WildGuard raw gaps are removed under the method, with F1 preserved.
- Boundary: not equal-cost, single-pass, or deployable-model SOTA.

### 1. Introduction

- Motivate safety judges as increasingly important moderation infrastructure.
- Explain the missing axis: social-pressure wrappers can push the desired label while keeping the underlying safety case fixed.
- State the counterfactual question: does the judge remain invariant to nuisance pressure interventions?
- Contributions:
  1. HARD V3 matched-neutral social-pressure contract.
  2. Plug-in post-hoc/test-time counterfactual neutralization estimator.
  3. Evaluation on selected accepted/direct baselines.
  4. Conservative claim gate and limitations.
- Include Figure 1 as the hero pipeline illustration.

### 2. Related Work

- Safety guard models and moderation benchmarks: WildGuard, HarmBench.
- Recent guard baselines: BingoGuard, HarmAug, DynaGuard.
- Robustness, calibration, and counterfactual controls.
- Positioning: unlike standard harmfulness or jailbreak evaluation, this paper isolates pressure-specific changes through matched neutral controls.

### 3. HARD V3 Contract and Plug-in Neutralization

- Define base content `C`, label `Y`, social-pressure wrapper `S`, and rendered input `X = render(C,S)`.
- Define matched neutral controls and primary pressure attacks.
- Define primary estimand: attack error minus matched-neutral error, aggregated over bases.
- Define the plug-in estimator.
- State cost boundary: it needs extra or cached neutral controls.
- Provide Algorithm 1.

### 4. Experiments

- Data/protocol: `hard_v3_core_balanced`, 50 bases, 2150 records per run, 1600 primary attacks, zero missing neutral controls.
- Baselines: DynaGuard, BingoGuard LLaMA3, HarmAug, WildGuard; ShieldLM supplementary only.
- Metrics: overall F1, attack F1, residual gate, primary gap, clean-correct flip, paired attenuation.
- Main result table: raw vs method.
- Attenuation figure/table for DynaGuard and WildGuard.
- WildGuard sparsity disclosure.

### 5. Analysis and Limitations

- Interpret raw-PASS and raw-FAIL baselines.
- Explain why `FAIL` after method is desirable: residual gap no longer clears vulnerability gate.
- Discuss cost/contract boundary.
- Discuss WildGuard sparse base-level improvement.
- Explicitly rule out broader SOTA claims.

### 6. Conclusion

- Reiterate the matched-neutral robustness contract and plug-in result.
- State that future work should evaluate equal-query or deployable variants and additional datasets.

## Figure And Table Plan

| ID | Type | Description | Data Source | Priority |
| --- | --- | --- | --- | --- |
| Fig. 1 | Method illustration | HARD V3 pipeline: base content, pressure attack, matched neutral controls, raw judge, counterfactual neutralizer, claim gate. | generated illustration | HIGH |
| Fig. 2 | Bar chart | Primary gap before and after counterfactual neutralization for the four selected main baselines. | claim_gate_summary.json | HIGH |
| Fig. 3 | Error-bar chart | Paired attenuation on DynaGuard and WildGuard with 95% CI and Holm-adjusted p-values. | attenuation JSONs | HIGH |
| Table 1 | LaTeX table | Raw baseline and method residual gate results with F1 and primary gap. | claim_gate_summary.json | HIGH |
| Table 2 | LaTeX table | Cost/contract boundary and unsafe claims. | STATUS docs | MEDIUM |

## Citation Plan

- Introduction and related work: WildGuard, HarmBench, BingoGuard, HarmAug, DynaGuard.
- Method: matched counterfactual/control framing and safety-judge evaluation.
- Current citation entries are provisional and must be verified before formal submission.

## Page Budget

| Section | Target pages |
| --- | ---: |
| Abstract | 0.25 |
| Introduction | 1.25 |
| Related Work | 1.00 |
| Method and Contract | 1.75 |
| Experiments | 2.25 |
| Analysis and Limitations | 1.00 |
| Conclusion | 0.35 |

## Review Status

Auto-review loop on the claim gate reached READY with score 8/10 for the exact limited claim. The paper must preserve the same limitation language.

