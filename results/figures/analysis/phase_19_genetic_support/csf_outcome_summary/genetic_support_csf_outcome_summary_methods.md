# Figure methods

The figure reads the validated biomarker `gate_decisions`, `status`, and
`checks` tables. Each of the 57 nuclear gene-by-biomarker tests is classified
from its stored `gate_state`, with the nearby-variant and MAGMA whole-gene
signal flags used to verify that classification. Counts are deterministic test
outcomes, so
uncertainty intervals and significance annotations are not applicable.

No P value is transformed or plotted. In particular, the stored APOE
amyloid-β 42 regional P value underflows to numerical zero, so the renderer
deliberately avoids `-log10(P)` geometry. Passing the regional and corrected
MAGMA tests is not relabeled as proof that the genetic signals share a variant
or as mechanistic validation. Blue and gray are supplemented by direct labels
and unit bars;
PDF and SVG are vector outputs and the PNG is exported at 450 DPI.
