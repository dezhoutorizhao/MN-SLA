# Paper Writing Pipeline Report

Date: 2026-05-01

Input sources:

```text
CLAIMS_FROM_RESULTS.md
outputs/hard_v3_method_claim_gate_20260501/claim_gate_summary.md
outputs/hard_v3_breakdowns_20260501/breakdown_report.md
docs/STATUS_2026-05-01_method_claim_gate.md
```

Target venue: ICLR-style ML conference paper.

## Pipeline Summary

| Phase | Status | Output |
| --- | --- | --- |
| Paper plan | complete | `PAPER_PLAN.md` |
| Narrative report | complete | `NARRATIVE_REPORT.md` |
| Figures | complete | `figures/` and `paper/figures/` |
| Breakdown analysis | complete | `outputs/hard_v3_breakdowns_20260501/` |
| LaTeX writing | complete | `paper/main.tex`, `paper/sections/*.tex` |
| Compilation | complete | `paper/main.pdf`, `paper/compile_status.md` |
| Nightmare review loop | in progress | latest terminal reviewer score 7.6/10 |

## Generated Figures And Tables

| Asset | File | Purpose |
| --- | --- | --- |
| Fig. 1 | `paper/figures/fig1_pipeline.pdf` | HARD V3 and post-hoc audit projection pipeline |
| Fig. 2 | `paper/figures/fig2_primary_gaps.pdf` | Raw vs projected primary gaps |
| Fig. 3 | `paper/figures/fig3_attenuation.pdf` | Paired attenuation for DynaGuard and WildGuard |
| Breakdown | `outputs/hard_v3_breakdowns_20260501/breakdown_report.md` | Family/layout/direction slices |
| Slice inference | `outputs/hard_v3_slice_inference_20260501/slice_inference.md` | Formal family/layout/direction inference and HarmAug continuous-score localization |

## Paper Structure

```text
0 Abstract
1 Introduction
2 Related Work
3 HARD V3 Contract and Audit Projection
4 Experiments
5 Analysis and Limitations
6 Conclusion
Appendix A Additional Experimental Details
```

## Claim Boundary Preserved

The draft uses the updated audit claim:

```text
Within the HARD V3 matched-neutral social-pressure robustness contract, the fixed post-hoc/test-time matched-control audit projection clears the selected-main-baseline claim gate: it makes the residual primary gap unsupported on raw vulnerability-supported main baselines (DynaGuard and WildGuard), shows Holm-adjusted positive paired attenuation, does not introduce a supported residual gap on raw vulnerability-not-supported main baselines (BingoGuard and HarmAug), and preserves overall/attack F1 under zero-drop tolerance. This is not an unrestricted SOTA, equal-cost, single-pass, or deployable-model claim.
```

The draft does not claim unrestricted SOTA, equal-cost SOTA, single-pass robustness, deployable-model superiority, trained PACT, or majority-base improvement for WildGuard.

## Verification

Static source checks passed:

```text
all required paper files exist and are non-empty
main.tex brace_balance 0
all section brace_balance 0
PYTHONPATH=src python -B -m unittest discover -s tests
Ran 120 tests
OK
```

Compilation succeeded with MiKTeX `pdflatex` + `bibtex`. The generated PDF is `paper/main.pdf` with 10 pages and 278815 bytes. See `paper/compile_status.md`.

## Remaining Work

- Visually inspect `paper/main.pdf`.
- Expand related work and validate citation metadata before submission.
- PKU200 DynaGuard/WildGuard remote runs are in progress and must be post-processed before they can upgrade the main evidence.
- Add broader non-PKU validation or a stronger main-compatible continuous-score baseline before claiming the 8.5 target or any broader SOTA-like result.
