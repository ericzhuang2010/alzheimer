# Methods: Phase 13 gene-support atlas

Gene interaction estimates were joined to the frozen module manifest by
`assay_feature_identifier` and to context-specific admitted genes from the
coverage table. Every admitted member was retained regardless of gene-level
P or q value. The same symmetric gene-effect display range, calculated as
the larger of 2 or the rounded 98th percentile of absolute admitted-member
effects, was applied to all four modules. Clipping is marked and exact
estimates, CIs, P values, and q values remain in plotted data.
