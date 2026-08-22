
Terminal-state counts were derived directly from `terminal_state` in
`recovery_route_decisions.tsv`. The route table was required to contain 54
unique route IDs spanning 27 nuclear candidate contexts, with exactly one eQTL
and one sQTL route per context. Counts were validated against
`recovery_status.tsv`; all blocking checks in `recovery_checks.tsv` were
required to pass. Route IDs and terminal states were matched one-to-one to the
54 rows in `recovery_colocalization_qc.tsv`, whose `posterior_rows` values were
required to be zero. `recovery_colocalization.tsv.gz` was required to retain its
declared H0-H4 columns while containing zero data rows. The graphic is a
terminal-outcome stacked bar—not a sequential attrition funnel—and was exported
at 12.4 × 4.7 inches as 450-DPI PNG plus editable PDF and SVG.
