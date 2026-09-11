# Harmonized broad-cell KDA: cross-cohort validation assessment

**Assessment date:** 2026-09-11  
**ROSMAP releases:** Phase 21 inputs and Phase 22 KDA  
**SEA-AD releases:** VH13 inputs and VH14 KDA  
**Computational status:** all four releases are `validated_complete` with zero
failed checks

## Executive conclusion

The workflow completed correctly, but the resulting evidence is not strong
enough to serve as convincing gene-level cross-cohort validation.

The prespecified validation unit was a key-driver gene in the same sex/APOE
group and the same broad cell class. Only one such stratum was tested by KDA in
both cohorts: `Astrocytes x F_e4`. ROSMAP returned 4 significant drivers and
SEA-AD returned 15, with no shared driver. If broad cell class is ignored but
sex/APOE group is retained, the shared-driver count is still zero.

If both stratification variables are ignored, the raw releases share two gene
symbols, `MT-ATP6` and `MT-ND4`. Both are mitochondrial-genome (`MT-*`) genes
and therefore violate the intended driver eligibility rule. After the minimum
unambiguous `MT-*` exclusion, the number of admissible shared driver genes is
**zero**.

This zero should be described as **inconclusive for cross-cohort key-driver
validation**, rather than as evidence that the biology does not replicate. The
comparison opportunity was extremely limited, no SEA-AD KDA call met the
plan's confirmatory-support threshold, and the two cohorts used different
disease endpoints and different Bayesian networks.

The result remains useful as a feasibility and attrition audit. It shows where
the current validation design loses comparable tests and identifies a necessary
driver-candidate correction before these releases can be treated as final.

## Analysis definition

The two tracks used the same high-level analysis design:

- donor-level broad-cell raw-count pseudobulk;
- at least 20 nuclei per donor x broad-cell profile;
- at least 3 donors in each disease arm for contrast eligibility;
- a separate disease contrast within each of six sex/APOE groups and seven
  broad cell classes;
- one deduplicated, merged up/down query containing core-mitochondrial DEGs at
  within-contrast FDR below 0.05, with no fold-change cutoff;
- at least 3 effective query genes after network mapping;
- the same fKDA settings and within-call BH driver FDR below 0.05; and
- cohort-specific broad-cell Bayesian networks.

The native disease endpoints were not identical: ROSMAP tested `AD - NCI`,
whereas SEA-AD tested `Dementia - No dementia`. The plan also defined at least
10 donors per arm as confirmatory support. Contrasts below that threshold may
be computationally estimable, but they are not confirmatory evidence.

## Attrition and output summary

| Quantity | ROSMAP | SEA-AD |
|---|---:|---:|
| Structural broad-cell x sex/APOE slots | 42 | 42 |
| Source DEG contrasts estimable | 42 (100%) | 28 (66.7%) |
| Source contrasts not estimable | 0 | 14 |
| Empty DEG queries | 27 | 21 |
| Nonempty queries lost after mapping or the 3-gene minimum | 12 | 2 |
| KDA calls executed | 3 (7.1% of structural slots) | 5 (11.9% of structural slots; 17.9% of estimable contrasts) |
| Executed calls with confirmatory donor support | 2 | 0 |
| Candidate tests across executed calls | 380 | 883 |
| Significant driver rows | 39 | 24 |
| Unique raw driver genes | 39 | 21 |
| Unique drivers after excluding `MT-*` | 33 | 18 |

For ROSMAP, 39 of 42 estimable contrasts never reached KDA: 27 had no
FDR-significant core-mitochondrial DEG, while another 12 had an empty or
smaller-than-three effective network-mapped query. For SEA-AD, 14 structural
contrasts were already untestable because of donor support; of the 28 estimable
contrasts, 23 failed to reach KDA.

The seven SEA-AD slots with confirmatory donor support all had empty queries.
Consequently, every executed SEA-AD KDA call was in the
`standard_nonconfirmatory_support` tier.

## Executed calls

| Cohort | Broad cell | Group | Disease/control donors | Support tier | Effective query | Significant drivers |
|---|---|---|---:|---|---:|---:|
| ROSMAP | Astrocytes | F_e4 | 26 / 11 | Confirmatory | 8 | 4 |
| ROSMAP | OPCs | F_e4 | 24 / 11 | Confirmatory | 3 | 9 |
| ROSMAP | Vasculature cells | M_e2 | 4 / 3 | Exploratory minimum-3 | 78 | 26 |
| SEA-AD | Astrocytes | F_e4 | 9 / 5 | Standard nonconfirmatory | 9 | 15 |
| SEA-AD | Excitatory neurons | M_e33 | 9 / 10 | Standard nonconfirmatory | 43 | 6 |
| SEA-AD | Inhibitory neurons | M_e33 | 9 / 10 | Standard nonconfirmatory | 45 | 1 |
| SEA-AD | Microglia | M_e33 | 9 / 10 | Standard nonconfirmatory | 5 | 1 |
| SEA-AD | Oligodendrocytes | M_e33 | 9 / 10 | Standard nonconfirmatory | 21 | 1 |

The call distribution is highly asymmetric. ROSMAP executed `F_e4` and `M_e2`
calls, whereas SEA-AD executed `F_e4` and `M_e33` calls. Their only exact
common stratum was `Astrocytes x F_e4`, and that stratum was confirmatory in
ROSMAP but nonconfirmatory in SEA-AD.

The ROSMAP result is also numerically dominated by the low-support
`Vasculature cells x M_e2` call. It contributed 78 of the 89 effective query
genes used in executed ROSMAP calls (87.6%) and 26 of 39 significant driver
rows (66.7%). Thus, the larger ROSMAP driver count is not evidence that ROSMAP
contains a broader validated signal; much of it comes from one exploratory
4-versus-3-donor comparison with a much larger query.

## Cross-cohort overlap

| Comparison rule | Observed overlap | Interpretation |
|---|---:|---|
| Same driver + same broad cell + same sex/APOE | 0 | No exact validation event |
| Same driver + same sex/APOE, ignoring broad cell | 0 | No group-level replication |
| Same driver anywhere, before driver eligibility filtering | 2 | `MT-ATP6`, `MT-ND4`; both disallowed `MT-*` genes |
| Same admissible non-`MT-*` driver anywhere | 0 | Descriptive gene-only Jaccard = 0/51 = 0 |

The two raw overlaps do not represent replication of a sex/APOE-specific
driver. In ROSMAP they arose in the exploratory `Vasculature cells x M_e2`
call. In SEA-AD they arose in `M_e33` neuronal and/or glial calls. They therefore
differ in sex/APOE group as well as broad-cell context.

The current KDA releases allowed query genes, including `MT-*` genes, to be
tested and returned as drivers. Six of 39 ROSMAP driver rows and six of 24
SEA-AD driver rows begin with `MT-`; the SEA-AD rows represent three unique
genes because `MT-ATP6` recurs across several broad classes. Some of these rows
are explicitly marked as signature genes in the call returns. This confirms
that a driver-side exclusion was not enforced.

The non-`MT-*` counts above are a transparent post hoc sensitivity summary, not
a corrected final KDA release. If prohibited candidates are removed, the
within-call BH family changes. A compliant release should enforce the driver
universe before multiple-testing correction, or reconstruct and recalculate
the correction over the permitted candidates.

This report uses `^MT-` as the minimum objective exclusion. Before a rerun, the
biological rule must be frozen more precisely: exclude only mitochondrial-genome
genes, exclude every core-mitochondrial query gene, or exclude all genes with a
specified mitochondrial annotation. Broader definitions may remove additional
nuclear-encoded mitochondrial genes.

## Why the result is weak for validation

### 1. There was almost no matched test space

The intended design contained 42 structural strata, but only one exact stratum
produced KDA results in both cohorts. A validation rate cannot be estimated
meaningfully from one opportunity. Skipped or empty-query strata are missing
comparisons, not negative validation tests.

### 2. SEA-AD supplied no confirmatory KDA calls

All five SEA-AD calls had fewer than 10 donors in at least one disease arm.
They can generate hypotheses, but under the plan's own evidence hierarchy they
cannot provide confirmatory replication. Lowering the eligibility threshold
does not create biological replication; it trades more coverage for less
stable donor-level inference.

### 3. Thresholded KDA calls are sensitive to query size and topology

Effective query sizes ranged from 3 to 78. Larger queries create different
neighborhood overlaps and testing behavior than very small queries. In
addition, each cohort used its own Bayesian network, with different node sets,
edges, and candidate-test universes. A driver mismatch may therefore reflect a
different DEG query, a different network topology, or both. It cannot be
attributed uniquely to lack of biological replication.

### 4. The disease phenotypes are related but not identical

ROSMAP's `AD/NCI` contrast and SEA-AD's `Dementia/No dementia` contrast do not
define exactly the same biological endpoint. Discordance can arise from
clinical classification, neuropathology, cohort composition, or covariate
structure rather than failure of a driver mechanism.

### 5. Broad aggregation solved one problem, not all problems

Moving from SEA-AD supertypes to seven broad classes removed fine-cell label
fragmentation and increased cells per donor profile. It did not repair sparse
sex/APOE disease arms, guarantee significant mitochondrial DEGs, or align the
cohort-specific networks. The limiting factor in this run was therefore not
that SEA-AD had too many supertypes.

### 6. “Every executed call was significant” is conditional evidence

All 3 ROSMAP and all 5 SEA-AD executed calls returned at least one driver at
within-call FDR below 0.05. Those calls were selected only after passing DEG,
network-mapping, and query-size gates, and FDR was controlled separately within
each call. This statement does not measure cross-cohort reproducibility and
should not be presented as validation success.

## Appropriate interpretation and use

The defensible interpretation is:

> The harmonized broad-cell workflow was technically successful, but it did
> not identify an admissible key-driver gene replicated between ROSMAP and
> SEA-AD. Because only one exact broad-cell/sex/APOE stratum was testable in
> both cohorts and SEA-AD had no confirmatory-support KDA call, the result is
> inconclusive rather than evidence of biological non-replication.

These releases should be retained as audited exploratory outputs. They are
useful for documenting sample-support limitations, DEG-query attrition,
network dependence, and the need for an explicit driver-candidate universe.
They should not be used as the main positive validation figure, and the two raw
`MT-*` overlaps should not be cited as validated drivers.

## Recommended next analysis

1. **Freeze the driver eligibility rule.** At minimum exclude `MT-*` symbols;
   decide explicitly whether all query genes or all mitochondrially annotated
   genes are also ineligible. Record the rule and candidate counts per call.
2. **Correct the KDA candidate families.** Apply the exclusion before
   within-call BH correction and regenerate new, non-overwriting derivative
   releases.
3. **Use a matched-strata table as the denominator.** For every broad-cell x
   sex/APOE stratum, distinguish `not estimable`, `empty query`, `query below
   minimum`, `executed nonconfirmatory`, and `executed confirmatory`. Calculate
   replication only among strata executed in both cohorts.
4. **Separate query disagreement from network disagreement.** As a sensitivity
   analysis, project each cohort's matched query through both cohort networks
   (a two-query x two-network design), or use one frozen common network. This
   reveals whether driver discordance is caused mainly by DEG selection or by
   topology.
5. **Make upstream and module-level concordance primary.** Compare broad-cell
   DEG effect directions/ranks and KDA neighborhood or module enrichment in
   matched strata. Exact thresholded driver-gene overlap is a stringent
   secondary endpoint, especially with independent networks.
6. **Do not solve sparse replication by silently lowering donor thresholds.**
   If more power is required, consider predeclared sex-only, APOE-carrier, or
   unstratified broad-cell sensitivity analyses. These answer broader questions
   and must remain separate from the six-group analysis.

## Reproducibility sources

- Plan: `docs/validation_human/harmonized_broad_kda/rosmap_phase21_22_seaad_vh13_14_broad_kda_plan.md`
- ROSMAP inputs/status: `results/minerva_production/21_harmonized_broad_kda_inputs/`
- ROSMAP KDA/driver table: `results/minerva_production/22_harmonized_broad_kda_combo/`
- SEA-AD inputs/status: `results/validation_human/13_harmonized_broad_kda_inputs/`
- SEA-AD KDA/driver table: `results/validation_human/14_harmonized_broad_kda_combo/`

No result directory was modified in producing this assessment.
