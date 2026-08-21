# SEA-AD two-class circular figures: methods

The renderer reads the compact validated VH10C selection contract: `status.tsv`, `seaad_top5.tsv`, `seaad_list_status.tsv`, `selection_checks.tsv`, `seaad_selection_freeze.tsv`, and their artifact registry. It verifies the registered SHA-256 values, `validated_complete` status, zero failed selection checks, `rosmap_candidate_files_read = False`, the frozen query/result tier, all candidate gates and stored ranks, and the 14-list testability grid against the 1,548-row SEA-AD KDA run manifest. The registered full `seaad_candidate_summary.tsv.gz` is not present and is not read; the renderer displays the already-frozen top lists and does not claim to rerank all 38,788 candidate units.

Candidate annotations are joined from the checksum-frozen Phase 18 annotation authority only to encode core-MitoCarta class, mtDNA dots, and extended-reference diamonds. No VH09 ROSMAP candidate table or VH10D overlap result is read. The selected set contains 8 MT and 5 non-MT network–gene units (11 unique symbols). MT-CO2 and MT-CYB recur across excitatory and inhibitory networks; recurrence curves connect the highest-uncapped-evidence occurrence to the other occurrence and are not Bayesian-network edges.

Both figures use the Phase 18 seven-network order, colorblind-aware palette, 35 fixed slots, clockwise geometry, 6° network gaps, 1° slot gaps, and common evidence cap of 15. Testable/no-passing lists use a solid medium-light gray track and direct label. Lists with no included KDA run use a darker dashed, cross-hatched track and direct label. Thus unavailable evidence is not represented as a negative biological result. SVG and PDF are vector exports; SVG preserves searchable text. PNG review copies are 5400 × 3240 at 450 DPI.

## Reproduction command

```bash
python scripts/figures/validation_human/plot_seaad_two_case_circular.py \
  --output-root results/figures/validation_human/seaad_two_case_circular \
  --visual-review-status pending
```
