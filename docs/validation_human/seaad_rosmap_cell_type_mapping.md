# SEA-AD–ROSMAP Cell-Type Mapping

SEA-AD does not use the same labels as the existing ROSMAP dataset, but it covers essentially all seven broad cell compartments in ROSMAP and is actually more granular at its deepest annotation level.

| Existing ROSMAP broad type | ROSMAP fine types | SEA-AD equivalent | SEA-AD supertypes |
|---|---:|---|---:|
| Astrocytes | 3 | Astrocyte | 6 |
| Excitatory neurons | 14 | 9 glutamatergic subclasses | 41 |
| Inhibitory neurons | 25 | 9 GABAergic subclasses | 67 |
| Immune cells | 5 | Microglia-PVM | 6 |
| OPCs | 1 | OPC | 3 |
| Oligodendrocytes | 1 | Oligodendrocyte | 4 |
| Vasculature | 5 | Endothelial and VLMC | 4 |

The apparent discrepancy comes from the hierarchy:

- ROSMAP: 7 broad types → 54 fine types.
- SEA-AD: 3 classes → 24 subclasses → 131 supertypes.

SEA-AD’s three classes collapse astrocytes, oligodendrocytes, OPCs, immune, and vascular cells into one top-level `Non-neuronal and Non-neural` class. Those lineages reappear in `Subclass`, so they are not actually absent.

The real limitation is label compatibility. ROSMAP uses marker-based names such as `Ast CHI3L1`, `Inh PVALB HTR4`, and `Mic P2RY12`, whereas SEA-AD often uses numbered labels such as `Astro_2`, `Pvalb_15`, and `Micro-PVM_2`. These are not automatically one-to-one biological matches.

For validation, the recommended approach is:

- Primary validation at the seven-broad-cell-type level.
- Secondary fine-cell validation only where marker expression supports a defensible crosswalk.
- Do not force all 54 ROSMAP fine types onto SEA-AD labels.

SEA-AD therefore has sufficient broad coverage for the project’s main external validation. Fine-type validation is possible, but it requires a marker-based taxonomy crosswalk rather than direct name matching.
