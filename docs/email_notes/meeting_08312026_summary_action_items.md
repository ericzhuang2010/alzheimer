# August 31, 2026 Meeting Summary and Professor Action Items

## Bottom line

The professor wants the project **simplified and refocused on sex differences**. The main next analysis should identify which key drivers are shared across groups and which are specific to a sex/APOE subgroup.

The clearest requested workflow is:

1. **Combine AD-up and AD-down mitochondrial DEGs into one unsigned query** for each fine-cell-type × sex/APOE comparison instead of running separate directional KDA queries.
2. **Rerun the ROSMAP KDA** with those combined queries.
3. Compare the resulting drivers across the six sex/APOE groups to identify **shared/common drivers and subgroup-specific drivers**, with particular attention to male-versus-female differences.
4. Present this comparison as a direct gene-by-group matrix or heatmap rather than relying mainly on the current recurrence summaries.
5. For cross-cohort validation, use a **cell-type- and sex/APOE-specific DEG comparison between ROSMAP and SEA-AD** as the practical next step. Do not describe SEA-AD KDA based on ROSMAP networks as an independent KDA validation.

The professor considered the extensive QTL/genetics follow-up less important right now because it is time-consuming and generally cannot resolve the sex/APOE subgroup specificity that is the current focus.

## What the professor wants you to do

### Priority 1 — Combine up- and downregulated mitochondrial DEGs and rerun KDA

The current analysis treats AD-up and AD-down mitochondrial signatures as two separate KDA directions. The professor repeatedly suggested combining them to make the analysis simpler and to avoid very small directional queries. Near the end of the meeting, the instruction was explicit: combine up and down, repeat the KDA, and then compare the results.

For the main ROSMAP analysis:

- Keep each fine cell type and sex/APOE group separate.
- Within each comparison, combine significant core-mitochondrial AD-up and AD-down genes into one query.
- Retain direction as an annotation if it may be useful later, but do not split the main KDA call by direction.
- Rerun KDA and regenerate the driver summaries from this new combined-query analysis.

This change would replace the current two directional slots per comparison with one combined KDA query per comparison.

*Key discussion: approximately 00:10:46–00:14:26 and 00:46:12–00:46:40.*

### Priority 2 — Revisit the minimum cell and query-size thresholds

The professor was uncomfortable with both of the current minimums:

- A DEG comparison can currently be attempted with as few as three cells/nuclei in each arm. The professor said that three is too small to be reliable and floated a substantially higher cell-count threshold.
- A KDA query can currently run with only three effective genes. The professor also considered this too small.

No final replacement threshold was firmly agreed upon. The professor's practical request was to try different values and determine how they affect both ROSMAP and SEA-AD, especially because SEA-AD is sparse.

**Concrete deliverable:** make a sensitivity table showing, for several minimum cell counts and effective query sizes:

- eligible comparisons and KDA runs;
- distribution across the six sex/APOE groups and cell types;
- number of returned drivers; and
- how severely SEA-AD coverage and imbalance change.

Use the combined up/down query when evaluating higher query-size cutoffs. Do not silently adopt a specific new cutoff until the sensitivity results are reviewed.

*Key discussion: approximately 00:05:46–00:06:30 and 00:12:12–00:15:38.*

### Priority 3 — Mine shared and subgroup-specific drivers directly

The professor wants the analysis to answer two questions clearly:

1. Which drivers are common across sex/APOE groups?
2. Which drivers are specific to a particular sex or sex/APOE subgroup?

The current bar charts summarize recurrence, but they make group specificity difficult to see. The professor suggested a matrix/heatmap-style view:

- rows: driver genes;
- columns: the six sex/APOE groups;
- cells: whether the driver was returned and/or how many fine cell types support it;
- panels or separate plots: broad cell types, so cell-type context is retained.

Counts may be printed inside the cells. Sorting should place broadly shared drivers first and group-specific drivers next. A second summary can explicitly classify genes as shared across sexes, male-specific, female-specific, or limited to one sex/APOE group.

The current scientific emphasis should be **sex differences**, not just a long list of recurrent genes.

*Key discussion: approximately 00:23:29–00:28:36 and 00:43:06–00:43:36.*

### Priority 4 — Change the SEA-AD validation strategy

The current slides report 42 active SEA-AD KDA calls and compare their returned drivers with ROSMAP. During the discussion, it became clear that these calls use the ROSMAP broad-cell Bayesian networks. The professor said this is not a meaningful independent KDA validation: a true network/KDA replication would require networks constructed from the SEA-AD cohort itself.

The professor accepted a simpler and more appropriate near-term validation:

- Compare DEGs between ROSMAP and SEA-AD.
- Make the comparison within corresponding cell types and sex/APOE groups.
- Keep it cell-type-specific; do not collapse everything into a global overlap.
- Resolve and document how SEA-AD supertypes correspond to ROSMAP fine or broad cell types. The mapping is not one-to-one, so this limitation must be explicit.

Therefore:

- **Default next step:** matched DEG overlap/concordance between cohorts.
- **Optional larger project:** build SEA-AD-specific networks and then rerun SEA-AD KDA if a true KDA validation is still desired.
- The existing cross-cohort driver results can be described as exploratory convergence under a shared network framework, but not as independent network replication.

*Key discussion: approximately 00:29:49–00:32:32 and 00:44:12–00:46:12.*

### Priority 5 — Deprioritize the full human-genetics/QTL program

The genetics deck screened all 433 ROSMAP drivers and proposed gene-level testing, brain-QTL checks, and same-variant/colocalization analyses. The professor's response was that this downstream work would take a long time and is not the most important next task. Most of the available genetic evidence is not sex/APOE-subgroup-specific, so it does not directly answer the project's current question.

For now:

- Keep the existing genetics results as general supporting context.
- Do not make the full 433-gene QTL/colocalization pipeline the next work block.
- First complete the combined-query KDA and shared-versus-specific driver analysis.

The genetics work can be revisited for a short list of prioritized drivers after the subgroup analysis is stable.

*Key discussion: approximately 00:40:24–00:44:10.*

### Priority 6 — Make the mitochondrial-gene source explicit on the slides

The professor asked which database defined the mitochondrial and mitochondrial-related genes and was not sure it was visible on the slide. The source is **Human MitoCarta 3.0** in the project configuration.

Add the database name and version directly to the methods/workflow slide, not only as a link or citation. Also state that the KDA query uses the `core_mito_protein` tier and that mitochondrial candidate drivers are excluded from the reported non-MT driver summaries.

*Key discussion: approximately 00:02:24–00:03:04.*

### Priority 7 — Adjust the project pace around school

The professor said school/coursework should be the priority. It is acceptable for the research to proceed more slowly, with meetings approximately every two or three weeks. The professor viewed a manuscript/publication as a useful longer-term goal, but not as a reason to compromise schoolwork.

*Key discussion: approximately 00:07:21–00:08:08 and 00:47:49–00:48:39.*

## Recommended next deliverables, in order

1. A one-slide revised methods schematic showing:
   `MitoCarta 3.0 DEGs -> combine AD-up + AD-down -> one query per fine cell type × sex/APOE group -> KDA -> shared/specific driver comparison`.
2. A threshold-sensitivity table for minimum cells per comparison arm and minimum effective query genes.
3. The rerun ROSMAP combined-query KDA results.
4. Gene × sex/APOE heatmaps, faceted by broad cell type, plus an explicit shared/male-specific/female-specific/group-specific driver table.
5. A matched ROSMAP-versus-SEA-AD DEG comparison within corresponding cell types and sex/APOE groups.
6. An updated presentation that treats the existing SEA-AD KDA overlap cautiously and moves the long genetics/QTL program to future work.

Once the combined KDA and first heatmaps exist, the professor wants to discuss the exact presentation format.

## What was presented at this meeting

### ROSMAP KDA reaggregation

The slides described:

- 54 fine cell types × six sex/APOE groups × two directions = 648 planned slots;
- 295 completed KDA calls with at least three effective query genes;
- 689 non-mitochondrial gene × sex/APOE × broad-cell category units;
- 433 distinct returned driver genes across 32 populated categories; and
- recurrent genes including RPS15 and RPL11.

### SEA-AD analysis and cross-cohort comparison

The slides described:

- 1,548 planned SEA-AD directional slots but only 42 active calls;
- 40 of those 42 calls in the male APOE3/3 group;
- 96 non-mitochondrial category units representing 91 genes in only four populated categories;
- 35 of 91 SEA-AD genes also returned somewhere in ROSMAP; and
- eight exact gene × sex/APOE × broad-cell matches.

The presentation's own results showed that broad cell-type context transferred better than sex/APOE context. The professor's network-independence concern and SEA-AD's extreme imbalance mean these findings should be framed as descriptive/exploratory, not formal replication.

### Human-genetics support

The genetics slides screened all 433 ROSMAP drivers using published AD mappings, disease GWAS, and brain QTL resources. Eight genes had strong direct published evidence, while gene-level tests and formal same-variant analyses remained pending. The professor did not reject this work, but considered it lower priority than clarifying the sex-specific driver result.

## Decisions and cautions to carry forward

- Do not continue treating AD-up and AD-down as the main separate KDA analyses.
- Do not treat three cells or three query genes as automatically adequate; show threshold sensitivity.
- Do not claim that SEA-AD independently validates KDA when its calls use ROSMAP networks.
- Do not overinterpret the existing sex/APOE category matches, given SEA-AD's concentration in male APOE3/3.
- Do not let a long QTL/colocalization project displace the requested shared-versus-specific driver analysis.
- Preserve cell-type resolution in every cross-cohort comparison.

## Interpretation note

The raw transcript contains substantial automatic-transcription errors and no reliable speaker labels. The action items above were inferred from the question-and-answer flow and checked against the two August 31 slide decks. The strongest instructions are the late-meeting requests to combine up/down regulation, repeat KDA, compare shared versus group-specific drivers, and use matched DEG overlap as the simpler SEA-AD validation. Exact replacement thresholds were discussed but not finalized.

## Source files

- `meeting_08312026_recording_raw.txt`
- `../presentations/08312026/sex_apoe_kda_fine_broad_08312026.pptx`
- `../presentations/08312026/human_genetic_support_for_key_drivers_08312026.pptx`
