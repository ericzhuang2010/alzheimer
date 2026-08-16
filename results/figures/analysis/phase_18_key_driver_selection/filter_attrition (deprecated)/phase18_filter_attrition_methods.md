# Phase 18 filter-attrition figure methods

The renderer read the validated Phase 18 production status, artifact manifest, case manifest, filter funnel, complete candidate-test matrix, gene-case summary, and final candidate table. Recorded Phase 18 hashes and byte counts were verified before plotting. It did not rerun KDA, alter self-overlap corrections, recompute coverage, combine P values, adjust q values, or select candidates.

Filter 1 uses the authoritative overall native-filter run-slot row. Filter 2 was summarized by case from all 1,463,150 gene × included-run opportunities; explicit tests and valid explicit or implicit zero-overlap results count as usable, while absent-background and invalid results count as unavailable. Filters 3–5 use the authoritative sequential gene × broad-network × case funnel. Distinct-gene counts were derived within each case by retaining a symbol when at least one broad-network aggregate remained after the relevant sequential gate. Distinct counts were never summed across networks, and all-case unique genes were calculated by set union.

Counts are deterministic properties of the validated bundle, so uncertainty intervals and hypothesis tests are not applicable. Okabe–Ito case colors are supplemented by panel labels, exact text, outlines, and hatched removal boxes. SVG and PDF are vector outputs; the PNG is exported at the recorded resolution.
