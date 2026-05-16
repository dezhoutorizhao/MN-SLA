# Neutral-Control Validity Audit

This audit uses existing MN-SLA artifacts and emits aggregate counts plus salted hashes only. It is mechanical and behavioral sanity evidence, not blinded human semantic validation.

audit_passed: `True`

## Mechanical Summary

| dataset | bases | records | attack cells | missing cells | role failures | cue failures | metadata mismatches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| non_pku200_source_pair | 200 | 8600 | 800 | 0 | 0 | 0 | 0 |
| pku200_scale | 200 | 8600 | 800 | 0 | 0 | 0 | 0 |
| pku50_main_gate | 50 | 2150 | 200 | 0 | 0 | 0 | 0 |

## Clean-Neutral Behavior Sanity

| run | clean n | neutral n | clean error | neutral error | neutral-clean error | mean abs score diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dynaguard_non_pku200 | 200 | 2000 | 0.345000 | 0.366500 | 0.021500 | 0.050500 |
| dynaguard_pku200 | 200 | 1999 | 0.170000 | 0.176588 | 0.006588 | 0.041521 |
| dynaguard_pku50 | 50 | 500 | 0.140000 | 0.154000 | 0.014000 | 0.054000 |
| wildguard_non_pku200 | 200 | 2000 | 0.200000 | 0.197000 | -0.003000 | 0.008000 |
| wildguard_pku200 | 200 | 2000 | 0.235000 | 0.216000 | -0.019000 | 0.022000 |
| wildguard_pku50 | 50 | 500 | 0.160000 | 0.146000 | -0.014000 | 0.026000 |

## Claim Boundary

- Supports: mechanical matching, cue-removal scanner counts, and clean-neutral behavioral sanity over archived artifacts.
- Does not support: independent human semantic validation, source-general robustness, deployable defense, single-pass robustness, or residual elimination beyond the frozen 50-base gate.
