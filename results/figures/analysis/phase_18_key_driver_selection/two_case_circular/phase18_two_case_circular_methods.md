# Phase 18 two-class circular figures: methods

The renderer read `call_key_driver_returns.tsv` (SHA-256 `b917f70e6edcdf030f63e88ba8fbc5b22b80714599c12c80ea449e8c38bd51d8`) and deduplicated run-level rows to one `broad_network + key_driver + case_id` record. It retained records with `terminal_candidate_status = driver_candidate`, ranked them within broad network and driver class by ascending aggregate ACAT q, ascending aggregate ACAT P, and gene symbol, and displayed ranks 1-5 without backfilling.

Both figures use identical seven-network, 35-slot geometry and a common evidence cap of 15. Network identity is encoded by the outer color band and text label. The right-side legend does not obscure center links. SVG and PDF are authoritative vector exports; PNG review copies were rendered at 450 dpi.

## Reproduction command

```bash
Rscript --vanilla \
  scripts/figures/analysis/phase_18_key_driver_selection/ \
  visualize_phase18_two_case_circular.R \
  --input results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv \
  --output-dir results/figures/analysis/phase_18_key_driver_selection/two_case_circular \
  --top-per-network 5 \
  --evidence-cap 15 \
  --png-dpi 450
```
