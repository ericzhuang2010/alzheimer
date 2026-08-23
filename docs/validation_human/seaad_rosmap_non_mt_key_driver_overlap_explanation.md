# Why there is no shared non-MT top key driver between ROSMAP and SEA-AD
> **Historical diagnostic note (superseded 2026-08-22):** This diagnostic was
> written for the overwritten SEA-AD tier. The amended non-MT selection is
> summarized in [vh09_vh10_execution_summary.md](vh09_vh10_execution_summary.md).


## Purpose and scope

This note explains the zero non-MT intersection in the descriptive ROSMAP-versus-SEA-AD top-driver Venn diagram. It addresses two related questions:

1. Where were the ROSMAP non-MT key drivers detected?
2. Why did none of them become a selected SEA-AD non-MT key driver?

The key distinction is between a gene being absent, a comparison being impossible because of insufficient donor support, a gene having some KDA evidence, and a gene passing the complete cross-run candidate-selection procedure. These are not equivalent outcomes.

## Plain-language conclusion

The zero non-MT overlap is a mismatch between the two cohorts' **final selected driver lists**. It does not mean that the genes are absent from the other cohort or that SEA-AD disproved every ROSMAP result.

ROSMAP had substantially more usable sex/APOE and fine-cell-type comparisons. SEA-AD could not analyze several of the donor subgroups that contributed to the ROSMAP results. In the SEA-AD contexts that were analyzable, most ROSMAP drivers had no qualifying KDA support, and the few with support appeared in only one run and did not survive cross-run aggregation and multiple-testing correction.

The result can be summarized as follows:

| Step | Number of ROSMAP non-MT network-gene units |
|---|---:|
| Selected by ROSMAP Phase 18 | 21 |
| Assessable in the corresponding SEA-AD network | 17 |
| Not testable in SEA-AD because there were no included OPC runs | 4 |
| Assessable units with at least one qualifying SEA-AD supporting run | 4 |
| Assessable units with no qualifying SEA-AD supporting run | 13 |
| Units selected as SEA-AD drivers | 0 |

The 21 ROSMAP units represent 15 unique genes because the same gene can be selected in more than one broad network. The SEA-AD non-MT list contains five units and five genes. Their gene-level intersection is zero.

## What insufficient SEA-AD subgroup data means

A stratum is one sex-by-APOE group. For example, `M_e4` means male APOE ε4 carriers. The SEA-AD protocol requires at least five independent donors in both the Dementia and No-dementia arms before fitting a direct disease contrast.

| Sex/APOE group | Dementia donors | No-dementia donors | Direct contrast possible? |
|---|---:|---:|---|
| Female APOE ε2 (`F_e2`) | 1 | 6 | No |
| Female APOE ε3/ε3 (`F_e33`) | 13 | 13 | Yes, subject to fine-type support |
| Female APOE ε4 (`F_e4`) | 9 | 5 | Yes, subject to fine-type support |
| Male APOE ε2 (`M_e2`) | 1 | 4 | No |
| Male APOE ε3/ε3 (`M_e33`) | 9 | 10 | Yes, subject to fine-type support |
| Male APOE ε4 (`M_e4`) | 4 | 3 | No |

Therefore, `F_e2`, `M_e2`, and `M_e4` were structurally not estimable in SEA-AD. This is a lack of enough **independent donors** in the corresponding disease arms. It is not necessarily a lack of nuclei, expression of the gene, or the relevant cell type. Donors are the statistical replicates; thousands of nuclei from a few donors cannot replace missing independent donors.

The earlier statement that "20 of the 21 ROSMAP non-MT selected units received support from at least one `F_e2`, `M_e2`, or `M_e4` stratum" means:

- ROSMAP support for those drivers included one or more sex/APOE comparisons that ROSMAP could analyze.
- SEA-AD did not have enough donors to run the corresponding comparisons.
- Consequently, SEA-AD could not attempt a like-for-like validation of that portion of the ROSMAP evidence.

It does **not** mean that all 20 units were supported exclusively by unavailable groups. Some also had ROSMAP support in potentially estimable SEA-AD groups. Those units still required a nonempty mitochondrial DEG query and qualifying KDA evidence in SEA-AD.

Only two of the 21 ROSMAP units had any ROSMAP supporting run in `M_e33`, whereas 40 of the 42 SEA-AD KDA calls came from `M_e33`. Thus, the two cohorts concentrated their usable evidence in different sex/APOE contexts.

### Concrete examples

- The ROSMAP Microglia result for `RPL11` was supported in `Mic P2RY12`, `M_e4`, AD-down. SEA-AD had only four Dementia and three No-dementia male ε4 donors, so this exact comparison could not be performed.
- The four ROSMAP OPC units (`RPS15`, `FTL`, `ANKRD11`, and `NCOA1`) were not testable as SEA-AD KDA candidates because SEA-AD produced no eligible OPC KDA run.
- A not-testable result must not be described as a failed replication. No valid SEA-AD KDA comparison existed for that unit.

## Where the selected ROSMAP non-MT drivers were found

The ROSMAP Phase 18 non-MT selections are listed below in their within-network rank order.

| ROSMAP broad network | Selected non-MT drivers |
|---|---|
| Astrocytes | 1. `RPL11`; 2. `RPLP1`; 3. `RPL15`; 4. `APOE`; 5. `LAPTM4A` |
| Excitatory neurons | 1. `RPL11`; 2. `RPS13`; 3. `SELENOW`; 4. `LAMTOR5`; 5. `DYNLT1` |
| Inhibitory neurons | 1. `RPS15`; 2. `LAMTOR5`; 3. `RPLP1`; 4. `ATP6V1F`; 5. `RPL38` |
| Microglia | 1. `RPL11` |
| OPCs | 1. `RPS15`; 2. `FTL`; 3. `ANKRD11`; 4. `NCOA1` |
| Oligodendrocytes | 1. `RPL11` |
| Vasculature | No selected non-MT driver |

Their ROSMAP support was distributed across fine-cell types and strata:

- Astrocyte drivers were supported in `Ast CHI3L1`, `Ast DPP10`, and/or `Ast GRM3`, predominantly in e2 or male ε4 strata, with some female ε4 support.
- Excitatory drivers were supported across multiple RORB-, THEMIS-, NRGN-, and RELN-related fine cell types. Individual drivers had support in 2–11 fine types.
- Inhibitory drivers were supported across LAMP5-, PVALB-, SST-, VIP-, and related fine cell types, with much of the evidence occurring in AD-down runs.
- The Microglia `RPL11` result came from `Mic P2RY12`, `M_e4`, AD-down.
- The OPC drivers came from OPC runs in `F_e33`, `M_e2`, and/or `F_e4`.
- The Oligodendrocyte `RPL11` result came from `Oli`, `M_e2`, AD-down.

## What happened to those ROSMAP drivers in SEA-AD

Seventeen of the 21 ROSMAP units belonged to the common assessable universe in SEA-AD. None passed all SEA-AD driver-candidate gates.

Only four had a qualifying SEA-AD within-run return in the same broad network:

| ROSMAP-selected unit | SEA-AD supporting fine type and contrast | Within-run q | Query overlap | Fold enrichment | Final outcome |
|---|---|---:|---:|---:|---|
| Excitatory `DYNLT1` | `L2/3 IT_10`, `M_e33`, AD-down | 0.0274 | 2 | 39.81 | Not selected after cross-run aggregation |
| Inhibitory `RPS15` | `Pvalb_2`, `M_e33`, AD-down | 0.0108 | 3 | 29.53 | Not selected after cross-run aggregation |
| Inhibitory `RPLP1` | `Pvalb_2`, `M_e33`, AD-down | 0.0305 | 4 | 9.56 | Not selected after cross-run aggregation |
| Inhibitory `RPL38` | `Lamp5_Lhx6_1`, `M_e33`, AD-down | 0.0100 | 3 | 35.70 | Not selected after cross-run aggregation |

These four units passed the coverage and conservative-support requirements but were not SEA-AD driver candidates. Under the frozen selector, the remaining failed gate is the aggregate ACAT BH threshold of q ≤ 0.05. Each had support in only one SEA-AD run, whereas several ROSMAP selections were supported repeatedly across many fine cell types and strata.

The other 13 assessable ROSMAP units had no qualifying published SEA-AD within-run return in the matching broad network. They therefore failed the requirement for at least one conservative supporting run.

This also shows that the zero overlap was not caused by the top-five display cap. None of these 17 assessable units became a SEA-AD driver candidate before ranking or display.

## Where the five SEA-AD non-MT drivers were found in ROSMAP

The reverse lookup leads to the same conclusion: most SEA-AD genes had some ROSMAP evidence, but none passed the complete ROSMAP Phase 18 candidate gates in the corresponding network.

| SEA-AD selected driver and network | ROSMAP aggregate p | ROSMAP BH q | Conservative supporting runs | ROSMAP outcome |
|---|---:|---:|---:|---|
| Excitatory `HGSNAT` | 0.00574 | 0.641 | 1 of 97 | Exploratory; not a candidate |
| Inhibitory `BEX3` | 0.000409 | 0.157 | 4 of 28 | Exploratory; not a candidate |
| Inhibitory `RPS27A` | 0.00882 | 1.000 | 2 of 28 | Exploratory; not a candidate |
| Inhibitory `RPL30` | 0.0193 | 1.000 | 0 of 28 | Exploratory; no conservative support |
| Oligodendrocyte `KANSL1L` | 1.000 | 1.000 | 0 of 2 | No explicit/supporting ROSMAP evidence |

Additional raw-return context is important:

- `BEX3` appears in raw ROSMAP Excitatory, Inhibitory, and OPC KDA returns.
- `HGSNAT` appears in raw ROSMAP Excitatory returns.
- `RPS27A` appears in raw ROSMAP Excitatory and Inhibitory returns.
- `RPL30` has two raw Inhibitory `M_e33` up-regulated returns, but both came from query-size-3 runs excluded by the ROSMAP minimum-query-size-10 rule. Both also had query overlap of only one gene, below the conservative-support requirement of two.
- `KANSL1L` has no significant primary ROSMAP KDA return.

A raw significant KDA return is not the same as a Phase 18-selected key driver. Final selection requires adequate coverage, at least one conservative supporting run, aggregate ACAT evidence, network-wide BH q ≤ 0.05, and then within-class ranking.

## Why the final lists differ

The main contributing factors are:

1. **Different donor support across sex/APOE groups.** SEA-AD could not estimate `F_e2`, `M_e2`, or `M_e4`, while these groups contributed heavily to the ROSMAP selections.
2. **Different numbers of usable KDA runs.** ROSMAP had 161 included Phase 18 runs; SEA-AD had 42. By network, ROSMAP versus SEA-AD had 21 versus 1 Astrocyte runs, 97 versus 20 Excitatory runs, 28 versus 16 Inhibitory runs, 6 versus 1 Microglia runs, 6 versus 0 OPC runs, 2 versus 4 Oligodendrocyte runs, and 1 versus 0 Vasculature runs.
3. **Different concentration of evidence.** Forty of the 42 SEA-AD calls came from `M_e33`. ROSMAP evidence was distributed much more broadly across groups and fine-cell types.
4. **Different recurrence across runs.** Several ROSMAP non-MT drivers had repeated support across fine-cell types and groups. Their SEA-AD counterparts generally had zero supporting runs or only one.
5. **A large non-MT candidate universe and stringent correction.** Thousands of genes are assessable in each broad network. A nominal aggregate p-value below 0.05 is insufficient when the aggregate results are corrected with BH across the network-wide candidate family.
6. **Not a class-definition or display artifact.** The cohorts used the same MT-versus-non-MT class definition and compatible Phase 18 selection rules. The relevant genes failed before the top-five display stage.

## Recommended interpretation

The result should be reported as:

> No non-MT gene was shared between the final cohort-specific top-driver lists. Four ROSMAP OPC units were not testable in SEA-AD, and most remaining ROSMAP units lacked recurrent SEA-AD KDA support. The zero overlap therefore reflects limited SEA-AD subgroup coverage, different fine-cell/stratum evidence, and stringent cross-run selection; it is not evidence that all ROSMAP non-MT biology was contradicted in SEA-AD.

Avoid the stronger but unsupported statement that the non-MT drivers "failed replication." The evidence contains three distinct outcomes:

- **Not testable:** no valid SEA-AD KDA run existed for the unit.
- **Tested but not selected:** the unit was assessable but did not pass all candidate gates.
- **Selected in both cohorts:** no non-MT unit met this definition.

The Venn diagram is a descriptive gene-level view that collapses broad-network membership. The primary replication unit remains broad network + gene + driver class in the common assessable universe.

## Authoritative result files

- SEA-AD donor-group counts: [`results/validation_human/02_cohort/donor_group_counts.tsv`](../../results/validation_human/02_cohort/donor_group_counts.tsv)
- Frozen ROSMAP selected units: [`results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv`](../../results/validation_human/09_rosmap_kda_candidates/phase18_selected_candidate_units.tsv)
- ROSMAP Phase 18 aggregate evidence: [`results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv`](../../results/minerva_production/18_key_driver_selection/call_key_driver_returns.tsv)
- SEA-AD KDA run manifest: [`results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10a_inputs/seaad_kda_run_manifest.tsv)
- SEA-AD significant KDA returns: [`results/validation_human/10_seaad_kda_rediscovery/10b_kda/seaad_kda_significant_returns.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10b_kda/seaad_kda_significant_returns.tsv)
- SEA-AD selected top drivers: [`results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10c_seaad_selection/seaad_top5.tsv)
- Strict ROSMAP-versus-SEA-AD unit trace: [`results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv`](../../results/validation_human/10_seaad_kda_rediscovery/10d_overlap/rosmap_seaad_candidate_overlap.tsv)

The locally downloaded compact VH10C package does not contain the registered full `seaad_candidate_summary.tsv.gz`. Consequently, exact SEA-AD aggregate p/q values cannot be tabulated for every failed ROSMAP unit from this checkout. The conclusions above use the frozen overlap classifications, list statuses, run manifest, and significant-return table; the four aggregate-q failures follow logically from the frozen gate definitions and their observed coverage/support status.
