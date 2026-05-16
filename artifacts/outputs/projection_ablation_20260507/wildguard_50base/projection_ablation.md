# HARD V3 Projection Ablation

This is an exploratory no-inference ablation over existing prediction artifacts.
It tests whether the matched-cell audit projection is more informative than simple or deliberately mismatched projections.
It is not a SOTA claim, not an equal-cost deployment result, and not a replacement for the frozen main claim gate.

| variant | scope | overall F1 | attack F1 | primary gap | p | attenuation | attenuation p | dropped pairs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | no_projection | 0.838819 | 0.831183 | 0.040625 | 0.020698 | NA | NA | NA |
| matched_mean | same_base_same_split_same_layout_same_format | 0.860374 | 0.859813 | 0.002500 | 0.500150 | 0.038125 | 0.019998 | 0.000000 |
| matched_first | same_base_same_split_same_layout_same_format_first_control | 0.860374 | 0.859813 | 0.002500 | 0.500150 | 0.038125 | 0.019998 | 0.000000 |
| matched_median | same_base_same_split_same_layout_same_format_median | 0.860374 | 0.859813 | 0.002500 | 0.500150 | 0.038125 | 0.019998 | 0.000000 |
| matched_trimmed_mean_10pct | same_base_same_split_same_layout_same_format_trimmed_mean | 0.860374 | 0.859813 | 0.002500 | 0.500150 | 0.038125 | 0.019998 | 0.000000 |
| matched_majority | same_base_same_split_same_layout_same_format_majority_vote | 0.860374 | 0.859813 | 0.002500 | 0.500150 | 0.038125 | 0.019998 | 0.000000 |
| clean_carry_forward | same_base_clean_prediction | 0.854428 | 0.851852 | 0.012500 | 0.502250 | 0.028125 | 0.076192 | 0.000000 |
| base_neutral_mean | same_base_same_split_all_neutrals | 0.866404 | 0.867925 | -0.007500 | 1.000000 | 0.048125 | 0.019998 | 0.000000 |
| global_neutral_mean | same_split_all_neutrals_all_bases | 0.705055 | 0.666667 | 0.352500 | 0.000100 | -0.311875 | 1.000000 | 0.000000 |
| same_cell_other_base_mean | same_split_same_layout_same_format_other_bases | 0.705055 | 0.666667 | 0.352500 | 0.000100 | -0.311875 | 1.000000 | 0.000000 |
| wrong_layout_same_base_mean | same_base_same_split_different_layout_or_format | 0.866404 | 0.867925 | -0.007500 | 1.000000 | 0.048125 | 0.019998 | 0.000000 |

Interpretation rule: a useful matched-control result should be compared against clean carry-forward, base-only, global, other-base, and wrong-layout projections before being discussed as evidence that the matching contract matters.
