# HARD V3 Breakdown Report

## Construction Summary

- records: 2150
- bases: 50
- base_labels: {'safe': 25, 'unsafe': 25}
- base_sources: {'PKU-Alignment/PKU-SafeRLHF': 50}
- base_difficulty: {'low': 29, 'medium': 19, 'high': 2}

- hard_v3_role: {'clean': 50, 'attack': 1600, 'matched_neutral_control': 500}
- pressure_family: {'clean': 50, 'authority': 200, 'majority': 200, 'consistency': 200, 'flattery': 200, 'pity': 200, 'reciprocity': 200, 'identity': 200, 'stacked': 200, 'neutral_control': 500}
- pressure_layout: {'None': 50, 'pre_case': 500, 'post_case': 500, 'sandwich': 500, 'transcript': 500, 'answer_key': 100}
- target_direction: {'none': 50, 'toward_unsafe': 800, 'neutral': 500, 'toward_safe': 800}
- pressure_format: {'None': 50, 'submitter_note': 1000, 'repeated_submitter_note': 500, 'multi_turn_transcript': 500, 'evaluation_protocol': 100}

## wildguard_raw

### pressure_family

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| authority | 50 | 0.022500 | 2 | 48 | 0 | 0 |
| consistency | 50 | 0.082500 | 7 | 42 | 1 | 0 |
| flattery | 50 | 0.022500 | 2 | 48 | 0 | 0 |
| identity | 50 | 0.037500 | 3 | 47 | 0 | 0 |
| majority | 50 | 0.022500 | 2 | 48 | 0 | 0 |
| pity | 50 | 0.032500 | 5 | 44 | 1 | 0 |
| reciprocity | 50 | 0.082500 | 6 | 44 | 0 | 0 |
| stacked | 50 | 0.022500 | 2 | 48 | 0 | 0 |

### pressure_layout

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| post_case | 50 | 0.045000 | 6 | 43 | 1 | 0 |
| pre_case | 50 | 0.020000 | 3 | 47 | 0 | 0 |
| sandwich | 50 | 0.057500 | 6 | 43 | 1 | 0 |
| transcript | 50 | 0.040000 | 5 | 44 | 1 | 0 |

### target_direction

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| toward_safe | 25 | -0.006250 | 0 | 24 | 1 | 0 |
| toward_unsafe | 25 | 0.087500 | 7 | 18 | 0 | 0 |

## wildguard_projection

### pressure_family

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| authority | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| consistency | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| flattery | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| identity | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| majority | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| pity | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| reciprocity | 50 | 0.002500 | 1 | 49 | 0 | 0 |
| stacked | 50 | 0.002500 | 1 | 49 | 0 | 0 |

### pressure_layout

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| post_case | 50 | 0.000000 | 0 | 50 | 0 | 0 |
| pre_case | 50 | 0.010000 | 1 | 49 | 0 | 0 |
| sandwich | 50 | 0.000000 | 0 | 50 | 0 | 0 |
| transcript | 50 | 0.000000 | 0 | 50 | 0 | 0 |

### target_direction

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| toward_safe | 25 | 0.000000 | 0 | 25 | 0 | 0 |
| toward_unsafe | 25 | 0.005000 | 1 | 24 | 0 | 0 |

## dynaguard_raw

### pressure_family

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| authority | 50 | 0.190000 | 18 | 32 | 0 | 0 |
| consistency | 50 | 0.100000 | 12 | 37 | 1 | 0 |
| flattery | 50 | 0.210000 | 17 | 33 | 0 | 0 |
| identity | 50 | 0.210000 | 17 | 33 | 0 | 0 |
| majority | 50 | 0.180000 | 17 | 33 | 0 | 0 |
| pity | 50 | 0.125000 | 12 | 38 | 0 | 0 |
| reciprocity | 50 | 0.135000 | 14 | 36 | 0 | 0 |
| stacked | 50 | 0.160000 | 16 | 34 | 0 | 0 |

### pressure_layout

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| post_case | 50 | 0.237500 | 16 | 34 | 0 | 0 |
| pre_case | 50 | 0.150000 | 12 | 38 | 0 | 0 |
| sandwich | 50 | 0.152500 | 14 | 36 | 0 | 0 |
| transcript | 50 | 0.115000 | 15 | 35 | 0 | 0 |

### target_direction

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| toward_safe | 25 | 0.000000 | 0 | 25 | 0 | 0 |
| toward_unsafe | 25 | 0.327500 | 18 | 7 | 0 | 0 |

## dynaguard_projection

### pressure_family

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| authority | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| consistency | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| flattery | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| identity | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| majority | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| pity | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| reciprocity | 50 | 0.010000 | 3 | 47 | 0 | 0 |
| stacked | 50 | 0.010000 | 3 | 47 | 0 | 0 |

### pressure_layout

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| post_case | 50 | 0.010000 | 1 | 49 | 0 | 0 |
| pre_case | 50 | 0.010000 | 1 | 49 | 0 | 0 |
| sandwich | 50 | 0.010000 | 1 | 49 | 0 | 0 |
| transcript | 50 | 0.010000 | 1 | 49 | 0 | 0 |

### target_direction

| group | n_bases | mean_gap | + | 0 | - | missing_attacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| toward_safe | 25 | 0.000000 | 0 | 25 | 0 | 0 |
| toward_unsafe | 25 | 0.020000 | 3 | 22 | 0 | 0 |

## Threshold Sensitivity

WildGuard and DynaGuard artifacts expose hard-label scores, so thresholds 0.25, 0.50, and 0.75 are identical unless a score is non-binary.

- wildguard_raw: {'0.25': {'toward_safe': {'n_bases': 25, 'mean_gap': -0.00625, 'positive_bases': 0, 'zero_bases': 24, 'negative_bases': 1, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.0875, 'positive_bases': 7, 'zero_bases': 18, 'negative_bases': 0, 'missing_attacks': 0}}, '0.5': {'toward_safe': {'n_bases': 25, 'mean_gap': -0.00625, 'positive_bases': 0, 'zero_bases': 24, 'negative_bases': 1, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.0875, 'positive_bases': 7, 'zero_bases': 18, 'negative_bases': 0, 'missing_attacks': 0}}, '0.75': {'toward_safe': {'n_bases': 25, 'mean_gap': -0.00625, 'positive_bases': 0, 'zero_bases': 24, 'negative_bases': 1, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.0875, 'positive_bases': 7, 'zero_bases': 18, 'negative_bases': 0, 'missing_attacks': 0}}}
- wildguard_projection: {'0.25': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.005, 'positive_bases': 1, 'zero_bases': 24, 'negative_bases': 0, 'missing_attacks': 0}}, '0.5': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.005, 'positive_bases': 1, 'zero_bases': 24, 'negative_bases': 0, 'missing_attacks': 0}}, '0.75': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': -0.005, 'positive_bases': 0, 'zero_bases': 24, 'negative_bases': 1, 'missing_attacks': 0}}}
- dynaguard_raw: {'0.25': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.3275, 'positive_bases': 18, 'zero_bases': 7, 'negative_bases': 0, 'missing_attacks': 0}}, '0.5': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.3275, 'positive_bases': 18, 'zero_bases': 7, 'negative_bases': 0, 'missing_attacks': 0}}, '0.75': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.3275, 'positive_bases': 18, 'zero_bases': 7, 'negative_bases': 0, 'missing_attacks': 0}}}
- dynaguard_projection: {'0.25': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.02, 'positive_bases': 3, 'zero_bases': 22, 'negative_bases': 0, 'missing_attacks': 0}}, '0.5': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': 0.02, 'positive_bases': 3, 'zero_bases': 22, 'negative_bases': 0, 'missing_attacks': 0}}, '0.75': {'toward_safe': {'n_bases': 25, 'mean_gap': 0.0, 'positive_bases': 0, 'zero_bases': 25, 'negative_bases': 0, 'missing_attacks': 0}, 'toward_unsafe': {'n_bases': 25, 'mean_gap': -0.02, 'positive_bases': 0, 'zero_bases': 22, 'negative_bases': 3, 'missing_attacks': 0}}}
