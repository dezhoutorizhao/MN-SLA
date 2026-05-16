# Claims From Results

Date: 2026-05-09

## Verdict

claim_supported: partial-to-yes under the narrow MN-SLA audit claim.

confidence: high for the bounded artifact-level claim; medium for broader practical mitigation interpretation.

## Supported Claims

- MN-SLA defines and executes a matched-neutral safety-label audit where pressure attacks are compared with same-base neutral controls, and inference is over bases rather than rendered prompts.
- Under the frozen 50-base selected-main gate, DynaGuard and WildGuard have supported raw pressure-specific gaps.
- Under the same 50-base selected-main gate, CF-Neutralize is a diagnostic matched-control readout that makes the DynaGuard and WildGuard residual primary gaps unsupported while preserving the paper's F1 sanity checks.
- BingoGuard and HarmAug are raw-vulnerability-not-supported guardrail baselines; their results support non-introduction of a supported residual gap, not vulnerability removal.
- PKU200, PKU2K full-data, and non-PKU200 diagnostics support raw vulnerability replication and strong attenuation evidence beyond the 50-base artifact.
- MN-SLA-Gated and the neutral-consensus selective-wrapper replay provide a secondary offline mitigation diagnostic that descriptively reduces measured error on auto-decided subsets while reporting abstention and induced-error costs.

## Unsupported Claims

- No broad or unrestricted SOTA claim.
- No equal-cost or single-pass robustness claim.
- No deployable-model superiority claim.
- No trained PACT or trained mitigation claim.
- No unique estimator optimality claim for mean-v1.
- No source-general robustness conclusion from the non-PKU source-pair audit.
- No residual-elimination claim at PKU200 or PKU2K scale for mean-v1.
- No claim that PKU2K replaces the frozen 50-base selected-main claim gate.
- No claim of completed blinded human validation of neutral controls.

## Missing Evidence

- Blinded human validation for neutral-control label preservation, perceived difficulty preservation, and pressure-cue removal, with inter-annotator agreement.
- Fresh preregistered larger/source-decoupled audit if the project wants broader generalization or residual-elimination claims.
- Fresh preregistered estimator-variant audit if cycle-v1 or other distributional variants are to become main claims.

## Suggested Paper Claim

The safe paper claim is: MN-SLA contributes a protocol-bounded matched-neutral safety-label audit for pressure-specific safety-judge sensitivity, with base-level inference and a fail-closed evidence-to-claim gate; selected raw-vulnerable baselines replicate raw pressure gaps and show strong matched-control attenuation, while scale diagnostics and wrapper replays remain diagnostic rather than claim-expanding evidence.
