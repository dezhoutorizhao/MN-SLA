# HARD V3 Projection Ablation

This is an exploratory no-inference ablation over existing prediction artifacts.
It tests whether the matched-cell audit projection is more informative than simple or deliberately mismatched projections.
It is not a SOTA claim, not an equal-cost deployment result, and not a replacement for the frozen main claim gate.

| variant | scope | overall F1 | attack F1 | primary gap | p | attenuation | attenuation p | dropped pairs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | no_projection | 0.864762 | 0.862444 | 0.009375 | 0.093991 | NA | NA | NA |
| matched_mean | same_base_same_split_same_layout_same_format | 0.868409 | 0.867347 | 0.005000 | 0.502250 | 0.004375 | 0.252475 | 0.000000 |
| matched_first | same_base_same_split_same_layout_same_format_first_control | 0.872693 | 0.873096 | 0.000000 | 0.749825 | 0.009375 | 0.252475 | 0.000000 |
| matched_median | same_base_same_split_same_layout_same_format_median | 0.868409 | 0.867347 | 0.005000 | 0.502250 | 0.004375 | 0.252475 | 0.000000 |
| matched_trimmed_mean_10pct | same_base_same_split_same_layout_same_format_trimmed_mean | 0.868409 | 0.867347 | 0.005000 | 0.502250 | 0.004375 | 0.252475 | 0.000000 |
| matched_majority | same_base_same_split_same_layout_same_format_majority_vote | 0.872693 | 0.873096 | 0.000000 | 0.749825 | 0.009375 | 0.252475 | 0.000000 |
| clean_carry_forward | same_base_clean_prediction | 0.860808 | 0.857143 | 0.015000 | 0.254375 | -0.005625 | 0.717028 | 0.000000 |
| base_neutral_mean | same_base_same_split_all_neutrals | 0.874096 | 0.875000 | -0.005000 | 0.752125 | 0.014375 | 0.217778 | 0.000000 |
| global_neutral_mean | same_split_all_neutrals_all_bases | 0.350037 | 0.000000 | 0.375000 | 0.000100 | -0.365625 | 1.000000 | 0.000000 |
| same_cell_other_base_mean | same_split_same_layout_same_format_other_bases | 0.292579 | 0.059880 | 0.660000 | 0.000100 | -0.650625 | 1.000000 | 0.000000 |
| wrong_layout_same_base_mean | same_base_same_split_different_layout_or_format | 0.870735 | 0.870466 | 0.000000 | 0.752125 | 0.009375 | 0.217778 | 0.000000 |

Interpretation rule: a useful matched-control result should be compared against clean carry-forward, base-only, global, other-base, and wrong-layout projections before being discussed as evidence that the matching contract matters.
