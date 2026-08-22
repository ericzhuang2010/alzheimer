# Phase 19 Tier 2 recovery fixtures

`synthetic_lbf.tsv` is a tiny model-shape fixture used to document the
expected released SuSiE LBF orientation: variants are rows, signals are
columns, and the analysis transposes this to signal-by-variant before adding an
explicit zero log-Bayes-factor null column. The executable test generates
larger deterministic shared- and distinct-signal controls in memory.
