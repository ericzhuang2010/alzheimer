# Methods

The renderer reads the validated production tables `phase20_broad_status.tsv`, `phase20_broad_checks.tsv`, `phase20_broad_artifacts.tsv`, `phase20_broad_direction_manifest.tsv`, `phase20_broad_non_mt_candidates.tsv`, and `phase20_broad_top5_summary.tsv` from `results/minerva_production/20_sex_apoe_kda_broad`. Registered source hashes are verified before plotting.

The seven plotted candidate tiles are an exact key-level copy of rows flagged `top5_display = TRUE` in the 12-row relaxed candidate table and stored in `phase20_broad_top5_summary.tsv`. The renderer does not rerank candidates. The upstream order is the direct within-run order, and at most ranks 1–5 are displayed. Candidate gates are query overlap ≥ 2, fold enrichment > 1, non-core-MT within-run BH q ≤ 0.10, and exclusion of core mitochondrial genes; the strict reference uses q ≤ 0.05. The empty completed run annotation comes from `phase20_broad_direction_manifest.tsv`.

Tiles use Okabe-Ito blue for strict direct-reference candidates and hatched orange for relaxed-only candidates. The latter remains in the legend even though all seven displayed rows are strict. The figure is exported as a 300-DPI PNG and as vector SVG and PDF files, with plot data, validation checks, status, and artifact hashes saved alongside it.
