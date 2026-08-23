# SEA-AD two-class circular figures: methods

The renderer reads the compact validated VH10C selection contract: `status.tsv`, `seaad_top5.tsv`, `seaad_list_status.tsv`, `selection_checks.tsv`, `seaad_selection_freeze.tsv`, and their artifact registry. It verifies the registered SHA-256 values, `validated_complete` status, zero failed selection checks, consistency of the configured query/result tier and selection gates, stored ranks, and the 14-list testability grid against the 1,548-row SEA-AD KDA run manifest. The active result is explicitly labeled `posthoc_exploratory__fdr_only__donor3__query3__coverage80__q05` and is a post-hoc exploratory tier, not a confirmatory analysis. VH10C records `rosmap_candidate_files_read = False`; this provenance flag is reported without characterizing the post-hoc analysis as a blinded study. The registered full `seaad_candidate_summary.tsv.gz` is not present and is not read; the renderer displays the validated top lists and does not claim to rerank all 38,788 candidate units.

The query rule is `fdr_only_query_sensitivity` (FDR-only DEG query); effective queries require at least 3 genes. Candidate selection requires coverage ≥ 0.8, aggregate ACAT BH q ≤ 0.05, and at least 1 conservative supporting run. Candidate annotations are joined from the checksum-frozen Phase 18 annotation authority only to encode core-MitoCarta class, mtDNA dots, and extended-reference diamonds. No VH09 ROSMAP candidate table or VH10D overlap result is read by the renderer. The selected set contains 8 MT and 3 non-MT network–gene units (9 unique symbols). Repeated selected genes are MT-CO2 (MT drivers, 2 networks), MT-CYB (MT drivers, 2 networks). Recurrence curves connect the highest-uncapped-evidence occurrence to each other within-class occurrence and are not Bayesian-network edges.

Both figures use the Phase 18 seven-network order, colorblind-aware palette, 35 fixed slots, clockwise geometry, 6° network gaps, 1° slot gaps, and common evidence cap of 15. Testable/no-passing lists use a solid medium-light gray track and direct label. Lists with no included KDA run or no eligible class runs use a darker dashed, hatched track and direct label. Thus unavailable evidence is not represented as a negative biological result. SVG and PDF are vector exports; SVG preserves searchable text. PNG review copies are 5400 × 3240 at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_two_case_circular.py \
  --output-root results/figures/validation_human/seaad_two_case_circular \
  --visual-review-status pending
```
