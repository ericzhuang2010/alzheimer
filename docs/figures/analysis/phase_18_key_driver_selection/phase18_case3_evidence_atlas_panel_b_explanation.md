# Phase 18 Case 3 evidence atlas: Panel B column explanation

Panel B summarizes evidence breadth and reproducibility for each gene,
restricted to that gene's passing Case 3 network contexts.

From left to right:

1. **Broad networks (max 7)**  
   Number of broad cell-type networks in which the gene passed all Case 3
   driver gates. This includes passing contexts below the circle's top-five
   display cap. For example, RPS15 has 3 because its excitatory-neuron context
   passed even though it was not displayed in the circle.

2. **Fine cell types (max 16 observed)**  
   Number of unique fine cell types containing at least one conservatively
   supporting query. Fine cell types are counted as a set union across the
   gene's passing broad networks.

3. **Supporting / usable queries**  
   Recurrence of conservative support:

   ```text
   conservatively supporting runs / usable runs
   ```

   A run is one fine cell type × sex/APOE group × AD direction. A supporting
   run must satisfy all Phase 18 support gates. The bar represents the
   fraction; the label gives the exact counts. Thus, `25/125` means 25 of 125
   usable queries supported the gene.

4. **Usable / eligible queries**  
   Evidence coverage:

   ```text
   runs with a valid gene-level result / eligible runs
   ```

   The bar shows the coverage fraction and the label preserves the counts. For
   example, `125/126` means only one eligible query lacked a usable result.
   This measures completeness, not significance.

5. **Sex/APOE groups (max 6)**  
   Number of distinct primary sex/APOE groups with at least one conservatively
   supporting query:

   ```text
   F_e2, F_e33, F_e4, M_e2, M_e33, M_e4
   ```

   A value of 6 means support was observed in all six groups. It does not
   constitute a formal sex or APOE interaction test.

6. **AD directions (max 2)**  
   Number of mitochondrial signature directions with conservative support:

   ```text
   AD_up_mito
   AD_down_mito
   ```

   A value of 2 means the gene was supported by at least one AD-up query and
   at least one AD-down query.

For example, RPL11 has evidence in 4 broad networks, 15 fine cell types,
support in 25/125 usable queries, 125/126 coverage, all 6 sex/APOE groups, and
both AD directions.
