# Fine-cell DEG mitochondrial pathway analysis

This validated production bundle tests mitochondrial pathway over-representation
directly in ROSMAP fine-cell AD-versus-NCI DEG lists.

- Planned contrasts: 324
- Estimable contrasts: 321
- Query definitions: 972 (combined, AD-up, and AD-down)
- Legacy programs: 4
- Broad MitoCarta programs: 46
- Complete MitoCarta pathways: 149
- Primary ORA rows: 193428
- KDA-aligned effective queries: 194

The authoritative result is `fine_deg_pathway_ora.tsv.gz`; it includes
significant, nonsignificant, not-testable, empty-query, and non-estimable
records. Local BH FDR is primary. Global BH FDR is a study-wide sensitivity.

The KDA-aligned table is a downstream compatibility profile and must not be
confused with the pre-network primary DEG analysis. Enrichment is not proof
of pathway activity, driver control, or a disease-by-sex/APOE interaction.

