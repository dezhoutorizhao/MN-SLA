# HARD V3 Local Audit

This artifact is diagnostic only. It does not expand the main claim gate.

## Two-Sided Sensitivity

| run | metric | n | mean | one-sided p | two-sided p | +/0/- bases |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| dynaguard_raw | primary_attack_minus_matched_neutral_error | 50 | 0.163750 | 0.000100 | 0.000100 | 18/32/0 |
| dynaguard_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 43 | 0.174419 | 0.000100 | 0.000100 | 17/26/0 |
| dynaguard_raw | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.163750 | 0.000100 | 0.000100 | 18/32/0 |
| dynaguard_mean_v1 | primary_attack_minus_matched_neutral_error | 50 | 0.010000 | 0.124588 | 0.249575 | 3/47/0 |
| dynaguard_mean_v1 | primary_attack_clean_correct_excess_flip_over_matched_neutral | 43 | 0.011628 | 0.125787 | 0.253275 | 3/40/0 |
| dynaguard_mean_v1 | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.000000 | 1.000000 | 1.000000 | 0/50/0 |
| wildguard_raw | primary_attack_minus_matched_neutral_error | 50 | 0.040625 | 0.020698 | 0.039296 | 7/42/1 |
| wildguard_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 42 | 0.031994 | 0.015398 | 0.033197 | 6/36/0 |
| wildguard_raw | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.040625 | 0.020698 | 0.039296 | 7/42/1 |
| wildguard_mean_v1 | primary_attack_minus_matched_neutral_error | 50 | 0.002500 | 0.500150 | 1.000000 | 1/49/0 |
| wildguard_mean_v1 | primary_attack_clean_correct_excess_flip_over_matched_neutral | 42 | 0.002976 | 0.493251 | 1.000000 | 1/41/0 |
| wildguard_mean_v1 | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.000000 | 1.000000 | 1.000000 | 0/50/0 |
| bingoguard_raw | primary_attack_minus_matched_neutral_error | 50 | 0.010000 | 0.199780 | 0.384162 | 8/38/4 |
| bingoguard_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 47 | 0.007314 | 0.255274 | 0.529747 | 7/37/3 |
| bingoguard_raw | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.010000 | 0.199780 | 0.384162 | 8/38/4 |
| harmaug_raw | primary_attack_minus_matched_neutral_error | 50 | 0.009375 | 0.093991 | 0.188681 | 4/45/1 |
| harmaug_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 43 | 0.003634 | 0.247375 | 0.500150 | 2/41/0 |
| harmaug_raw | primary_attack_prob_drift_vs_matched_neutral | 50 | 0.013219 | 0.001400 | 0.003300 | 44/0/6 |
| dynaguard_pku200_raw | primary_attack_minus_matched_neutral_error | 200 | 0.134948 | 0.000100 | 0.000100 | 67/132/1 |
| dynaguard_pku200_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 166 | 0.146775 | 0.000100 | 0.000100 | 61/105/0 |
| dynaguard_pku200_raw | primary_attack_prob_drift_vs_matched_neutral | 200 | 0.134948 | 0.000100 | 0.000100 | 67/132/1 |
| dynaguard_pku200_mean_v1 | primary_attack_minus_matched_neutral_error | 200 | 0.007542 | 0.000500 | 0.000800 | 11/189/0 |
| dynaguard_pku200_mean_v1 | primary_attack_clean_correct_excess_flip_over_matched_neutral | 166 | 0.006074 | 0.008499 | 0.016498 | 7/159/0 |
| dynaguard_pku200_mean_v1 | primary_attack_prob_drift_vs_matched_neutral | 200 | 0.000000 | 1.000000 | 1.000000 | 0/200/0 |
| wildguard_pku200_raw | primary_attack_minus_matched_neutral_error | 200 | 0.028281 | 0.000100 | 0.000100 | 19/180/1 |
| wildguard_pku200_raw | primary_attack_clean_correct_excess_flip_over_matched_neutral | 153 | 0.013072 | 0.000700 | 0.001400 | 11/142/0 |
| wildguard_pku200_raw | primary_attack_prob_drift_vs_matched_neutral | 200 | 0.028281 | 0.000100 | 0.000100 | 19/180/1 |
| wildguard_pku200_mean_v1 | primary_attack_minus_matched_neutral_error | 200 | 0.003750 | 0.031297 | 0.061094 | 5/195/0 |
| wildguard_pku200_mean_v1 | primary_attack_clean_correct_excess_flip_over_matched_neutral | 153 | 0.000817 | 0.499750 | 1.000000 | 1/152/0 |
| wildguard_pku200_mean_v1 | primary_attack_prob_drift_vs_matched_neutral | 200 | 0.000000 | 1.000000 | 1.000000 | 0/200/0 |

## Matched-Control Coverage

| run | records | bases | cells | missing cells | nondivisible cells | duplicate ids | multi-label bases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dynaguard_raw | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| dynaguard_mean_v1 | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| wildguard_raw | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| wildguard_mean_v1 | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| bingoguard_raw | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| harmaug_raw | 2150 | 50 | 250 | 0 | 0 | 0 | 0 |
| dynaguard_pku200_raw | 8597 | 200 | 1000 | 0 | 1 | 0 | 0 |
| dynaguard_pku200_mean_v1 | 8597 | 200 | 1000 | 0 | 1 | 0 | 0 |
| wildguard_pku200_raw | 8600 | 200 | 1000 | 0 | 0 | 0 | 0 |
| wildguard_pku200_mean_v1 | 8600 | 200 | 1000 | 0 | 0 | 0 | 0 |

## Cycle Permutation Sensitivity

| run | permutations | min gap | median gap | max gap | share exact zero | share supported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dynaguard_pku200_raw | 40 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 |
| wildguard_pku200_raw | 40 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 |
