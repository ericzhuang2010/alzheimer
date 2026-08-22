# OPC RPS15 public-data-first execution report

**Execution date:** 2026-08-21  
**Backend:** local direct execution  
**Minerva used:** no  
**Author data required:** no  
**New downloaded source bytes:** 0  
**Final result directory:** `/home/ericzhuang2010/VscodeProjects/alzheimer/results/minerva_production/19_genetic_support_opc_rps15_public_recovery`

## Outcome

- Eligible routes measured for RPS15: 31
- Eligible routes with a source-significant RPS15 QTL: 6
- Routes with complete compatible model/LD inputs: 0
- Newly validated genes: 0
- Scientific outcome: `suggestive_public_support_only`

The already-local NG00184 chromosome-19 files were audited after the frozen
source/context gate was hashed. Released PIP and credible-set summaries were
retained as descriptive evidence, but were not renamed colocalization and did
not produce H4. No full archive was downloaded or streamed.

## Storage

- Existing NG00184 archives: approximately 4.0 GiB
- Frozen chromosome-19 member set: 280 files,
  210334198 bytes
- Compact RPS15 regional extract: `/home/ericzhuang2010/VscodeProjects/alzheimer/data/reference/phase19_genetic_support/opc_rps15_public_recovery/regional_extracts/opc_rps15_released_rows.tsv.gz`
- Work directory bytes: 3200
- New targeted-download bytes: 0
- Staging bytes before manifests: 493075

## Evidence boundary

Every signal-positive route lacked either a complete downloadable regional
summary-statistics object through a direct small public endpoint, a complete
fitted multi-signal QTL model, or source-matched ancestry-compatible LD.
Consequently primary SuSiE/coloc.susie analysis was not run. This is a valid
terminal public-data result and does not mean that RPS15 has no biological role.

See `opc_rps15_evidence_summary.tsv`, `opc_rps15_assessability.tsv`, and
`opc_rps15_acquisition_decisions.tsv` in the final result directory.
