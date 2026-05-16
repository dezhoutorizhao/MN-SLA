# HARD V3 Projection Ablation

This is an exploratory no-inference ablation over existing prediction artifacts.
It tests whether the matched-cell audit projection is more informative than simple or deliberately mismatched projections.
It is not a SOTA claim, not an equal-cost deployment result, and not a replacement for the frozen main claim gate.

| variant | scope | overall F1 | attack F1 | primary gap | p | attenuation | attenuation p | dropped pairs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | no_projection | 0.891115 | 0.887719 | 0.010000 | 0.199780 | NA | NA | NA |
| matched_mean | same_base_same_split_same_layout_same_format | 0.891962 | 0.888889 | 0.010000 | 0.252775 | 0.000000 | 0.526747 | 0.000000 |
| matched_first | same_base_same_split_same_layout_same_format_first_control | 0.895056 | 0.893023 | 0.005000 | 0.501450 | 0.005000 | 0.332067 | 0.000000 |
| matched_median | same_base_same_split_same_layout_same_format_median | 0.891962 | 0.888889 | 0.010000 | 0.252775 | 0.000000 | 0.526747 | 0.000000 |
| matched_trimmed_mean_10pct | same_base_same_split_same_layout_same_format_trimmed_mean | 0.891962 | 0.888889 | 0.010000 | 0.252775 | 0.000000 | 0.526747 | 0.000000 |
| matched_majority | same_base_same_split_same_layout_same_format_majority_vote | 0.891962 | 0.888889 | 0.010000 | 0.252775 | 0.000000 | 0.526747 | 0.000000 |
| clean_carry_forward | same_base_clean_prediction | 0.930568 | 0.941176 | -0.050000 | 0.967503 | 0.060000 | 0.002700 | 0.000000 |
| base_neutral_mean | same_base_same_split_all_neutrals | 0.891962 | 0.888889 | 0.010000 | 0.373863 | 0.000000 | 0.521748 | 0.000000 |
| global_neutral_mean | same_split_all_neutrals_all_bases | 0.712659 | 0.666667 | 0.390000 | 0.000100 | -0.380000 | 1.000000 | 0.000000 |
| same_cell_other_base_mean | same_split_same_layout_same_format_other_bases | 0.712659 | 0.666667 | 0.390000 | 0.000100 | -0.380000 | 1.000000 | 0.000000 |
| wrong_layout_same_base_mean | same_base_same_split_different_layout_or_format | 0.891962 | 0.888889 | 0.010000 | 0.373863 | 0.000000 | 0.521748 | 0.000000 |

Interpretation rule: a useful matched-control result should be compared against clean carry-forward, base-only, global, other-base, and wrong-layout projections before being discussed as evidence that the matching contract matters.
