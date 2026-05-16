# Novelty Check Report

Date: 2026-05-09

## Proposed Method

MN-SLA is a matched-neutral safety-label audit for social-pressure sensitivity in safety judges. It fixes the safety case and gold label, compares pressure wrappers against matched neutral controls, performs inference over bases, and gates claims through a fail-closed artifact predicate. CF-Neutralize remains a diagnostic matched-control readout; MN-SLA-Gated remains a secondary offline selective-wrapper replay.

## Core Claims

1. Matched-neutral safety-label estimand for social-pressure sensitivity: Novelty HIGH. Closest prior work shows judge artifact, prompt, persuasion, and robustness failures, but does not define this same fixed-case/fixed-label matched-neutral safety-label estimand.
2. Base-level inference plus fail-closed artifact/claim gate: Novelty MEDIUM-HIGH. The statistical pieces are not individually new, but the safety-judge claim predicate and artifact discipline are a strong differentiator.
3. CF-Neutralize diagnostic matched-control readout: Novelty MEDIUM. Novel only as residual-gap accounting under the MN-SLA contract, not as a deployable mitigation.
4. Neutral-consensus selective-wrapper replay: Novelty LOW-MEDIUM. Consensus and prompt-ensemble ideas are active prior work; the novelty is limited to the matched-neutral artifact replay and explicit abstention/induced-error accounting.
5. PKU200/PKU2K/non-PKU scale diagnostics: Novelty LOW. They strengthen evidence against sample-size artifacts but are not the method novelty and do not replace the frozen 50-base gate.

## Closest Prior Work

| Paper | Year | Overlap | Key Difference |
|---|---:|---|---|
| Know Thy Judge | 2025 | Safety-judge robustness meta-evaluation | Does not define MN-SLA's matched-neutral safety-label estimand or base-level claim gate |
| Safer or Luckier? | 2025 | Safety evaluators sensitive to artifacts | Studies artifact sensitivity broadly, not the matched pressure-vs-neutral safety-label estimand |
| CALM / Justice or Prejudice? | 2025 | Broad LLM-as-judge bias quantification | Principle-guided bias measurement, not social-pressure matched neutral controls |
| Trick the Grader | 2025 | Persuasion biases LLM judges | Math-grading persuasion rather than safety-label matched neutral audit |
| RobustJudge / TrustJudge / FairJudge | 2025-2026 | Judge robustness, inconsistency, calibration, aggregation | Broader reliability frameworks, not MN-SLA's pressure-specific safety-label gap |
| Auto-Prompt Ensemble / Beyond Consensus | 2025 | Prompt ensemble and consensus mitigation | General aggregation/mitigation; MN-SLA-Gated is only an offline matched-neutral replay |
| Causal Judge Evaluation | 2025 | Auditable judge-validity framing | Calibrated surrogate metrics and policy ranking rather than matched social-pressure estimand |

## Overall Assessment

Latest comparable novelty-check score before this patch series: 8/10 after the PKU2K sample-size framing edit. A subsequent stricter terminal Codex novelty pass reported 7.5/10 before the final related-work and wording patch; that number is a pre-patch diagnostic signal rather than a final post-patch regression score. Recommendation remains: PROCEED under a narrow protocol-bounded audit framing.

The main differentiator is not that judge models are artifact-sensitive. That broad phenomenon is prior work. The defensible novelty is the precise matched-neutral safety-label estimand, base-level inference unit, reproducible artifact ledger, and fail-closed evidence-to-claim gate.

## Actions Taken

- Added related-work connective tissue for Auto-Prompt Ensemble, Beyond Consensus, Causal Judge Evaluation, LLM judge principles, ObjexMT, and One Token to Fool LLM-as-a-Judge.
- Softened wording in the abstract, introduction, experiments, and conclusion to prevent broad novelty or mitigation overclaiming.
- Added wrapper base-level interval discussion as a stability diagnostic, not a selected-main wrapper gate.

## Source Notes

The novelty review used web and terminal Codex searches over arXiv, OpenReview, ACM/ICTIR metadata, ICLR pages, and project-local bibliography. The raw terminal review is archived at:

```text
outputs/codex_gpt55_high_novelty_check_final_mn_sla_20260509.txt
```
