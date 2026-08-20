# VH09 ROSMAP Phase 18 Candidate Freeze

**Status:** implemented and executed locally  
**Code:** `scripts/validation_human/09_freeze_rosmap_kda_candidates.py`  
**Configuration:** `scripts/validation_human/seaad_phase18_validation_config.yml`  
**Output:** `results/validation_human/09_rosmap_kda_candidates/`

## Purpose

VH09 freezes the Phase 18 discoveries that later SEA-AD phases will test. It
does not perform differential expression, network scoring, KDA, candidate
selection, or reranking.

The authoritative discovery input is the canonical Phase 18
`call_key_driver_returns.tsv`. Candidate units are keyed by:

```text
broad_network + key_driver + case_id
```

The primary validation set contains the 47 units with `top5_display = TRUE`.
These represent 25 unique genes. The 78 units with
`terminal_candidate_status = driver_candidate` are retained as a prespecified
sensitivity set.

## Inputs

- Canonical Phase 18 `call_key_driver_returns.tsv`
- Phase 18 selection process document, configuration, and implementation
- Validated VH08 status
- VH08 SEA-AD contrast manifest containing seven primary and 42 secondary slots

All six inputs are checksum-frozen in the VH09 configuration. Phase 12 is not
an analysis input or validation authority for VH09.

## Outputs

| File | End state |
|---|---|
| `phase18_selected_candidate_units.tsv` | 47 primary Phase 18 gene-network-class units |
| `phase18_passing_candidate_units.tsv` | 78 passing units for sensitivity analysis |
| `phase18_selected_genes.tsv` | 25 unique selected genes and their network memberships |
| `phase18_selected_directions.tsv` | 79 prespecified candidate-direction hypotheses |
| `seaad_candidate_validation_manifest.tsv` | Complete candidate-direction-by-SEA-AD-contrast plan |
| `candidate_freeze_checks.tsv` | Blocking count, identity, direction, and mapping gates |
| `artifacts.tsv` | Input, code, configuration, and output checksums |
| `status.tsv` | Terminal VH09 status and principal output checksums |

The complete validation manifest has 553 rows: every one of the 79 frozen
candidate-direction hypotheses is crossed with one pooled primary and six
sex/APOE secondary slots from its matching broad cell type. Rows are labeled
`planned_scoring` or `contrast_not_estimable`; no unavailable contrast is
silently omitted.

## Local command

```bash
cd /home/ericzhuang2010/VscodeProjects/alzheimer
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python scripts/validation_human/09_freeze_rosmap_kda_candidates.py \
  --config scripts/validation_human/seaad_phase18_validation_config.yml
```

VH09 is metadata-only and does not require Minerva.
