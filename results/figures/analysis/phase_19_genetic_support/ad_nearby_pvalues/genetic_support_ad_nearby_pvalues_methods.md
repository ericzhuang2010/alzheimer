
Values were read from the validated
`recovery_regional_gwas_summary.tsv` table for Bellenguez GWAS Catalog accession
`GCST90027158`. The source table was required to contain exactly one row for
each of 19 unique nuclear genes, and its run status and blocking checks were
required to pass. The exact source strings were retained for the displayed P
labels. For positive P values, `−log₁₀(P)` was computed directly and the source
regional-signal flag was checked against the frozen `P < 5e-8` rule. APOE’s
stored zero was treated only as numerical underflow: no finite `−log₁₀(P)` was
calculated or substituted. Filled blue diamonds identify the four values below
the cutoff; open gray circles and dotted lines identify the 15 values at or
above it, providing redundant shape and line-style encoding in addition to
color. These screening-cutoff positions guide follow-up without serving as
total-evidence ratings. Candidate windows extend 1 Mb on either side of the
gene span. The graphic was exported at
12.4 × 4.7 inches as a 450-DPI PNG plus editable PDF and SVG.
