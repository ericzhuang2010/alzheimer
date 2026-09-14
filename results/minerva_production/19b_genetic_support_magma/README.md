# Phase 19b MAGMA screen

This validated WS3 bundle contains 912 candidate-by-trait records for 228 genes
and four traits. MAGMA tested 832 records; 80 records retain explicit symbol or
FUMA-v110 reference-model limitations.

The frozen family-wise threshold is `0.05 / (228 × 4) = 5.48245614e-5`.
Six rows across APOE, INTS8, and PLCG2 pass. Clinical AD was run fresh with
MAGMA v1.10 and the official `g1000_eur` panel. The three unchanged CSF scans
were reused from the deprecated historical bundle only after exact result-file
checksum validation. Rebuildable `work/` intermediates remain local.
