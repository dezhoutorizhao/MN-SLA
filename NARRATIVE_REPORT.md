# Narrative Report: Counterfactual Social-Pressure Robustness for Safety Judges

## One-Sentence Thesis

Safety judges can be sensitive to social-pressure wrappers even when the underlying safety-relevant content is fixed; under the HARD V3 matched-neutral audit contract, a post-hoc matched-control projection makes selected residual pressure gaps unsupported without reducing F1.

## Problem

Modern guard models are commonly evaluated on harmfulness, jailbreak, or refusal datasets. These benchmarks usually ask whether a classifier recognizes unsafe content, but they do not isolate whether the classifier's decision changes when the same content is embedded in a social-pressure wrapper. HARD V3 defines this as a counterfactual robustness problem: keep the base content and gold safety label fixed, vary pressure wrappers, and compare attack variants against matched neutral controls.

## Method

The method is `test_time_counterfactual_neutralization_v1`, framed in the paper as a post-hoc/test-time matched-control audit projection. It does not train a new safety model. For every primary attack instance, it uses neutral controls matched by `base_id`, `pressure_layout`, and `pressure_format`, then evaluates the residual gap after replacing the pressure-side score with the matched neutral estimate.

This must be described as an audit estimator, not as a deployable single-pass guard model. It relies on extra or cached matched-neutral controls and therefore is not an equal-cost comparison against one-pass baselines.

## Data And Protocol

- Contract: HARD V3 matched-neutral social-pressure robustness.
- Main split: `hard_v3_core_balanced`.
- Scale: 50 bases, 2150 records per main run, 1600 primary attack records.
- Missing neutral controls: 0 for all selected main raw and method artifacts.
- Main baselines: DynaGuard, BingoGuard LLaMA3, HarmAug, WildGuard.
- Supplementary only: ShieldLM, because its official response-safety contract does not directly match rendered HARD V3 review prompts.

## Main Evidence

The claim gate reports `SUPPORTED_LIMITED_POSTHOC_AUDIT_CLAIM` with 64/64 OK checks. The selected main baselines have complete method-pair coverage. DynaGuard and WildGuard are raw vulnerability-supported baselines; BingoGuard and HarmAug are raw vulnerability-not-supported baselines.

Raw baseline results:

| Run | Gate | Overall F1 | Attack F1 | Primary Gap |
| --- | --- | ---: | ---: | --- |
| DynaGuard raw | V-SUP | 0.783528 | 0.758294 | 0.163750 [0.093750, 0.238750], p=0.000100 |
| BingoGuard LLaMA3 raw | V-NS | 0.891115 | 0.887719 | 0.010000 [-0.010000, 0.031250], p=0.199780 |
| HarmAug raw | V-NS | 0.864762 | 0.862444 | 0.009375 [0.000000, 0.021250], p=0.093991 |
| WildGuard raw | V-SUP | 0.838819 | 0.831183 | 0.040625 [0.006859, 0.090016], p=0.020698 |

Audit-projection results:

| Run | Gate | Overall F1 | Attack F1 | Residual Primary Gap |
| --- | --- | ---: | ---: | --- |
| DynaGuard + audit projection | R-NS | 0.860689 | 0.858369 | 0.010000 [0.000000, 0.022500], p=0.124588 |
| BingoGuard + audit projection | R-NS | 0.891962 | 0.888889 | 0.010000 [0.000000, 0.025000], p=0.252775 |
| HarmAug + audit projection | R-NS | 0.868409 | 0.867347 | 0.005000 [0.000000, 0.015000], p=0.502250 |
| WildGuard + audit projection | R-NS | 0.860374 | 0.859813 | 0.002500 [0.000000, 0.007500], p=0.500150 |

Paired attenuation for raw vulnerability-supported baselines:

| Baseline | Primary Error-Gap Attenuation | Clean-Correct Flip Attenuation |
| --- | --- | --- |
| DynaGuard | 0.153750 [0.087500, 0.227500], p=0.000100, Holm p=0.000300 | 0.162791 [0.095185, 0.239826], p=0.000100, Holm p=0.000300 |
| WildGuard | 0.038125 [0.004375, 0.080000], p=0.019998, Holm p=0.047095 | 0.029018 [0.007440, 0.056548], p=0.015698, Holm p=0.047095 |

WildGuard's result is statistically supported but sparse: primary attenuation has 7 positive bases, 42 zero bases, and 1 negative base, with median 0. The safe interpretation is positive paired mean attenuation, not majority-base improvement.

## Exact Supported Claim

Within the HARD V3 matched-neutral social-pressure robustness contract, the fixed post-hoc/test-time matched-control audit projection clears the selected-main-baseline claim gate: it makes the residual primary gap unsupported on raw vulnerability-supported main baselines (DynaGuard and WildGuard), shows Holm-adjusted positive paired attenuation, does not introduce a supported residual gap on raw vulnerability-not-supported main baselines (BingoGuard and HarmAug), and preserves overall/attack F1 under zero-drop tolerance. This is not an unrestricted SOTA, equal-cost, single-pass, or deployable-model claim.

## Limitations

The current result is protocol-bounded. It does not imply unrestricted SOTA, equal-query inference, single-pass robustness, deployable-model superiority, trained PACT, or majority-base improvement for WildGuard. The current 50-base evidence is strongest as an audit result; 8.5-level top-venue readiness would require a compiled PDF, broader related work, larger or cross-source HARD V3 validation, and deeper family-level inference.
