#!/usr/bin/env python3
"""Generate one concise Markdown structure summary per Seurat RDS JSON record."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "rds_structure_summary_bundle_v1"

OUTPUT_NAMES = {
    "astrocytes": "astrocytes_rds_summary.md",
    "excitatory_set1": "excitatory_neurons_set1_rds_summary.md",
    "excitatory_set2": "excitatory_neurons_set2_rds_summary.md",
    "excitatory_set3": "excitatory_neurons_set3_rds_summary.md",
    "immune": "immune_cells_rds_summary.md",
    "inhibitory": "inhibitory_neurons_rds_summary.md",
    "opcs": "opcs_rds_summary.md",
    "oligodendrocytes": "oligodendrocytes_rds_summary.md",
    "vasculature": "vasculature_cells_rds_summary.md",
}

TITLES = {
    "astrocytes": "Astrocytes RDS",
    "excitatory_set1": "Excitatory Neurons Set 1 RDS",
    "excitatory_set2": "Excitatory Neurons Set 2 RDS",
    "excitatory_set3": "Excitatory Neurons Set 3 RDS",
    "immune": "Immune Cells RDS",
    "inhibitory": "Inhibitory Neurons RDS",
    "opcs": "OPCs RDS",
    "oligodendrocytes": "Oligodendrocytes RDS",
    "vasculature": "Vasculature Cells RDS",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="results/rds_structure_summaries.json",
        help="Combined JSON created on Minerva",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/minerva",
        help="Directory for the nine Markdown files",
    )
    return parser.parse_args()


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def fmt_int(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def fmt_num(value: Any, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return "N/A"
    if number.is_integer():
        return fmt_int(number)
    return f"{number:,.{digits}f}"


def fmt_percent(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{100 * float(value):.1f}%"


def fmt_bytes(value: Any) -> str:
    if value is None:
        return "N/A"
    number = float(value)
    units = ("bytes", "KiB", "MiB", "GiB", "TiB")
    unit = units[0]
    for candidate in units:
        unit = candidate
        if abs(number) < 1024 or candidate == units[-1]:
            break
        number /= 1024
    precision = 0 if unit == "bytes" else 1
    return f"{number:,.{precision}f} {unit}"


def fmt_dim(value: Any) -> str:
    dimensions = as_dict(value)
    if not dimensions:
        return "Not populated"
    if "rows" in dimensions and "columns" in dimensions:
        return f"{fmt_int(dimensions['rows'])} × {fmt_int(dimensions['columns'])}"
    return " × ".join(fmt_int(item) for item in dimensions.values())


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(md_cell(item) for item in headers) + " |",
        "|" + "|".join("---" if i == 0 else "---:" for i in range(len(headers))) + "|",
    ]
    lines.extend("| " + " | ".join(md_cell(item) for item in row) + " |" for row in rows)
    return lines


def populated_layers(record: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    values: list[tuple[str, str, dict[str, Any]]] = []
    for assay_name, assay in as_dict(record.get("assays")).items():
        for layer_name, layer in as_dict(assay.get("layers")).items():
            values.append((assay_name, layer_name, as_dict(layer)))
    return values


def normalization_description(record: dict[str, Any]) -> tuple[str, list[str]]:
    commands = as_dict(record.get("commands"))
    normalize = next(
        (value for name, value in commands.items() if "NormalizeData" in name),
        None,
    )
    if normalize is None:
        return (
            "A populated `RNA@data` matrix is present, but no normalization command "
            "is retained in the object. The exact method and scale factor therefore "
            "cannot be proven from this RDS alone.",
            [],
        )
    parameters = as_dict(normalize.get("parameters"))
    method = parameters.get("normalization.method", "unknown")
    scale = parameters.get("scale.factor", "unknown")
    timestamp = normalize.get("timestamp", "not recorded")
    sentence = (
        f"The object retains `NormalizeData.RNA`: method `{method}`, scale factor "
        f"{fmt_int(scale)}, recorded at `{timestamp}`."
    )
    formula = [
        "For gene *i* in nucleus *j*, the stored LogNormalize transformation is:",
        "",
        "\\[",
        "\\ln\\left(1 + \\frac{\\mathrm{UMI}_{ij}}"
        "{\\mathrm{total\\ UMIs\\ in\\ nucleus\\ }j} \\times 10{,}000\\right)",
        "\\]",
    ] if method == "LogNormalize" and float(scale) == 10000 else []
    return sentence, formula


def tool_rows(record: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    tools = as_dict(record.get("tools"))
    integration = as_dict(tools.get("Integration"))
    anchors = as_dict(as_dict(integration.get("slots")).get("anchors"))
    if anchors:
        rows.append(
            [
                "`tools$Integration@anchors`",
                fmt_dim(anchors.get("dimensions")),
                "Internal Seurat integration anchor table; not donor/sample metadata",
            ]
        )
    transfer = as_dict(tools.get("TransferData"))
    weights = as_dict(as_dict(transfer.get("items")).get("weights.matrix"))
    if weights:
        rows.append(
            [
                "`tools$TransferData$weights.matrix`",
                fmt_dim(weights.get("dimensions")),
                f"Sparse transfer weights; {fmt_int(weights.get('nonzero_entries'))} nonzero entries",
            ]
        )
    for name, value in tools.items():
        if name not in {"Integration", "TransferData"}:
            rows.append(
                [f"`tools${name}`", fmt_dim(as_dict(value).get("dimensions")), "Additional Seurat tool data"]
            )
    return rows


def reduction_rows(record: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for name, reduction in as_dict(record.get("reductions")).items():
        assay_used = reduction.get("assay_used") or "not recorded"
        present = reduction.get("assay_used_is_present")
        note = f"Saved `{name}` cell embedding; assay used: `{assay_used}`"
        if present is False:
            note += ", but that assay is not stored"
        rows.append(
            [f"`reductions${name}`", fmt_dim(as_dict(reduction.get("cell_embeddings")).get("dimensions")), note]
        )
    return rows


def render(record_id: str, record: dict[str, Any], source_json: str) -> str:
    title = TITLES.get(record_id, record.get("source_file_name", record_id))
    overview = as_dict(record.get("overview"))
    metadata = as_dict(record.get("metadata"))
    coverage = as_dict(metadata.get("donor_cell_type_coverage"))
    nuclei_per_donor = as_dict(metadata.get("nuclei_per_donor"))
    obj = as_dict(record.get("object"))
    fine_types = as_list(metadata.get("fine_cell_type_summary"))
    layers = populated_layers(record)
    fields = as_list(metadata.get("fields"))
    reductions = reduction_rows(record)
    tools = tool_rows(record)

    lines: list[str] = [
        f"# {title}: Concise Structure Summary",
        "",
        f"This document summarizes `{record.get('source_file_name')}` from the completed Minerva inspection in "
        f"`{source_json}`. It describes structure and dimensions; it does not contain the expression matrices.",
        "",
        "## Overall dimensions",
        "",
    ]
    lines += table(
        ["Item", "Value"],
        [
            ["Seurat object", ", ".join(as_list(obj.get("class")))],
            ["Seurat object version", obj.get("version", "N/A")],
            ["File size on disk", fmt_bytes(record.get("source_file_bytes"))],
            ["Approximate size after loading in R", fmt_bytes(obj.get("object_size_bytes"))],
            ["Genes/features", fmt_int(overview.get("features"))],
            ["Nuclei (called cells by Seurat)", fmt_int(overview.get("nuclei"))],
            ["Donors (`projid`)", fmt_int(overview.get("donors"))],
            ["Fine cell types", fmt_int(overview.get("fine_cell_types"))],
            ["Observed donor × fine-cell-type combinations", fmt_int(coverage.get("observed_pairs"))],
            ["Possible donor × fine-cell-type combinations", fmt_int(coverage.get("possible_pairs"))],
            ["Donor × fine-cell-type coverage", fmt_percent(coverage.get("coverage_fraction"))],
            ["Active assay", f"`{obj.get('active_assay', 'N/A')}`"],
        ],
    )
    lines += [
        "",
        "Every nucleus has one nonmissing `projid` and one nonmissing "
        "`cell_type_high_resolution` value." if metadata.get("missing_donor_ids") == 0 and metadata.get("missing_fine_cell_types") == 0
        else "Some donor or fine-cell-type metadata values are missing; see the composition table below.",
        "",
        "## Components inside the RDS",
        "",
    ]

    component_rows: list[list[Any]] = []
    for assay_name, layer_name, layer in layers:
        biological = as_dict(layer.get("biological_coverage"))
        role = layer.get("role", "expression data")
        if role == "raw_counts":
            contents = (
                f"Raw UMI counts; {fmt_int(layer.get('nonzero_entries'))} nonzero entries; "
                f"{fmt_int(layer.get('total_raw_counts'))} total UMIs"
            )
        elif role == "normalized_expression":
            contents = f"Normalized expression; {fmt_int(layer.get('nonzero_entries'))} nonzero entries"
        else:
            contents = role.replace("_", " ")
        component_rows.append(
            [
                f"`{assay_name}@{layer_name}`",
                fmt_dim(layer.get("dimensions")),
                f"{fmt_int(biological.get('donors'))} donors; {fmt_int(biological.get('fine_cell_types'))} fine types",
                contents,
            ]
        )
    if not any(layer_name == "scale.data" for _, layer_name, _ in layers):
        component_rows.append(
            ["`RNA@scale.data`", "Not populated", "N/A", "No scaled or z-scored expression layer"]
        )
    component_rows.extend(
        [
            [
                "`RNA@meta.features`",
                fmt_dim(as_dict(as_dict(record.get("assays")).get("RNA")).get("feature_metadata", {}).get("dimensions")),
                "Gene-level",
                "Feature rows are present, but no feature-annotation columns are stored",
            ],
            [
                "`RNA@var.features`",
                f"Length {fmt_int(as_dict(as_dict(record.get('assays')).get('RNA')).get('variable_features', {}).get('count'))}",
                "Gene-level",
                "No saved variable-feature list" if as_dict(as_dict(record.get("assays")).get("RNA")).get("variable_features", {}).get("count") == 0 else "Saved variable-feature names",
            ],
            [
                "`meta.data`",
                fmt_dim(metadata.get("dimensions")),
                f"{fmt_int(overview.get('donors'))} donors; {fmt_int(overview.get('fine_cell_types'))} fine types",
                "Per-nucleus donor and fine-cell-type assignments",
            ],
            [
                "`active.ident`",
                f"Length {fmt_int(as_dict(record.get('active_identity')).get('length'))}",
                "Cell-level",
                "Matches fine-cell-type metadata" if as_dict(record.get("active_identity")).get("matches_fine_cell_type") else "Does not match fine-cell-type metadata",
            ],
        ]
    )
    for reduction in reductions:
        component_rows.append([reduction[0], reduction[1], "Cell-level", reduction[2]])
    lines += table(["Component", "Dimensions", "Biological coverage", "Contents"], component_rows)

    lines += [
        "",
        "## Fine-cell-type composition",
        "",
    ]
    type_rows = [
        [
            f"`{item.get('fine_cell_type')}`",
            fmt_int(item.get("nuclei")),
            fmt_int(item.get("donors")),
            fmt_int(item.get("missing_donor_ids")),
        ]
        for item in fine_types
    ]
    type_rows.append(
        ["**Total**", f"**{fmt_int(overview.get('nuclei'))}**", f"**{fmt_int(overview.get('donors'))} unique**", "**0**"]
    )
    lines += table(["Fine cell type", "Nuclei", "Donors represented", "Missing donor IDs"], type_rows)
    lines += [
        "",
        "Donor counts overlap across rows because one donor can contribute nuclei to several fine cell types. "
        "The donor column must not be summed.",
        "",
        "## Donor coverage across fine cell types",
        "",
    ]
    coverage_rows = [
        [fmt_int(item.get("fine_cell_types_per_donor")), fmt_int(item.get("donors"))]
        for item in as_list(coverage.get("donors_by_number_of_fine_cell_types"))
    ]
    coverage_rows.append(["**Total donors**", f"**{fmt_int(overview.get('donors'))}**"])
    lines += table(["Fine cell types represented for a donor", "Number of donors"], coverage_rows)

    lines += [
        "",
        "### Nuclei per donor",
        "",
    ]
    lines += table(
        ["Minimum", "First quartile", "Median", "Mean", "Third quartile", "Maximum"],
        [[
            fmt_num(nuclei_per_donor.get("minimum")),
            fmt_num(nuclei_per_donor.get("first_quartile")),
            fmt_num(nuclei_per_donor.get("median")),
            fmt_num(nuclei_per_donor.get("mean")),
            fmt_num(nuclei_per_donor.get("third_quartile")),
            fmt_num(nuclei_per_donor.get("maximum")),
        ]],
    )

    normalization_text, formula = normalization_description(record)
    lines += [
        "",
        "## Expression layers and normalization",
        "",
        "- `RNA@counts` contains raw UMI counts and should be used for donor-level pseudobulk count models.",
        "- `RNA@data` is populated and contains normalized expression values.",
        "- `RNA@scale.data` is not populated.",
        "",
        normalization_text,
    ]
    if formula:
        lines += [""] + formula

    lines += [
        "",
        "## Saved reductions and analysis helpers",
        "",
    ]
    if reductions:
        lines += table(["Component", "Dimensions", "Interpretation"], reductions)
    else:
        lines.append("No dimensionality reduction is stored. In particular, there is no saved PCA or UMAP.")
    lines += [""]
    if tools:
        lines += table(["Tool component", "Dimensions", "Interpretation"], tools)
    else:
        lines.append("No Seurat integration or transfer helper data are stored in `tools`.")

    graph_names = list(as_dict(record.get("graphs")))
    neighbor_names = list(as_dict(record.get("neighbors")))
    image_names = list(as_dict(record.get("images")))
    lines += [
        "",
        f"- Graphs: {', '.join(f'`{name}`' for name in graph_names) if graph_names else 'none'}",
        f"- Neighbor objects: {', '.join(f'`{name}`' for name in neighbor_names) if neighbor_names else 'none'}",
        f"- Spatial images: {', '.join(f'`{name}`' for name in image_names) if image_names else 'none'}",
    ]

    identity = as_dict(record.get("active_identity"))
    identity_levels = [str(item) for item in as_list(identity.get("levels"))]
    lines += [
        "",
        "## Metadata, identities, and sample information",
        "",
        f"The per-nucleus metadata contains exactly: {', '.join(f'`{field}`' for field in fields)}.",
        "",
    ]
    if identity.get("matches_fine_cell_type"):
        lines.append("`active.ident` matches `cell_type_high_resolution`, so Seurat's active grouping is the fine-cell-type label.")
    else:
        displayed = ", ".join(f"`{item}`" for item in identity_levels) or "no recorded levels"
        lines.append(
            f"`active.ident` does **not** match `cell_type_high_resolution`; its recorded level(s) are {displayed}. "
            "Use `cell_type_high_resolution` for cell-type grouping, or explicitly reset Seurat identities before an identity-based analysis."
        )
    lines += [
        "",
        "The RDS does **not** contain `specimenID`, `sampleID`, `libraryID`, sequencing batch, or a "
        "barcode-to-specimen mapping. The available cell-level relationship is:",
        "",
        "```text",
        "nucleus barcode -> projid + fine cell type",
        "```",
        "",
        "It is not possible to assign nuclei to multiple specimens or libraries using this RDS alone. "
        "Do not join a one-to-many biospecimen table to nuclei using only `projid`.",
        "",
        "Sex, diagnosis, APOE genotype, age, PMI, and `individualID` are also absent and must be joined "
        "from validated external donor metadata using `projid`.",
        "",
        "## Mitochondrial feature coverage",
        "",
    ]
    mt_present = as_list(overview.get("mitochondrial_protein_genes_present"))
    mt_missing = as_list(overview.get("mitochondrial_protein_genes_missing"))
    lines.append(
        f"All {fmt_int(len(mt_present))} canonical mtDNA-encoded protein genes are present."
        if not mt_missing
        else f"Present: {fmt_int(len(mt_present))}; missing: {', '.join(f'`{item}`' for item in mt_missing)}."
    )
    lines += [
        "",
        "## Important limitations",
        "",
        "- The independent biological units are donors identified by `projid`; nuclei from one donor are not independent people.",
        "- No specimen/library assignment or validated sequencing-batch covariate is stored.",
        "- Clinical and genotype variables require an external donor-level join.",
        "- No scaled expression, PCA, neighbor graph, or clustering graph is stored.",
    ]
    if reductions and any(item[2].endswith("but that assay is not stored") for item in reductions):
        lines.append(
            "- A saved embedding references an `integrated` assay that is absent; the embedding can be plotted, "
            "but the original integration cannot be reconstructed from this RDS alone."
        )
    if not identity.get("matches_fine_cell_type"):
        lines.append("- The active Seurat identity is not the fine-cell-type annotation and should not be used without resetting it.")

    lines += [
        "",
        "## Bottom line",
        "",
        f"`{record.get('source_file_name')}` contains raw and normalized RNA expression for "
        f"{fmt_int(overview.get('features'))} genes across {fmt_int(overview.get('nuclei'))} nuclei from "
        f"{fmt_int(overview.get('donors'))} donors and {fmt_int(overview.get('fine_cell_types'))} fine cell "
        "type(s). Donor-aware analyses should use `projid` as the biological replicate and "
        "`cell_type_high_resolution` as the cell-type label.",
        "",
    ]
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    bundle = json.loads(input_path.read_text(encoding="utf-8"))
    if bundle.get("schema_version") != EXPECTED_SCHEMA:
        raise SystemExit(
            f"Unsupported schema: {bundle.get('schema_version')!r}; expected {EXPECTED_SCHEMA!r}"
        )
    run = as_dict(bundle.get("run"))
    if run.get("status") != "complete" or run.get("completed_rds") != 9:
        raise SystemExit(f"Input bundle is not complete: {run}")
    objects = as_dict(bundle.get("objects"))
    missing = set(OUTPUT_NAMES) - set(objects)
    extra = set(objects) - set(OUTPUT_NAMES)
    if missing or extra:
        raise SystemExit(f"Unexpected object IDs; missing={sorted(missing)}, extra={sorted(extra)}")
    for record_id, output_name in OUTPUT_NAMES.items():
        record = as_dict(objects[record_id])
        if record.get("status") != "complete":
            raise SystemExit(f"Object {record_id!r} is not complete")
        text = render(record_id, record, input_path.as_posix())
        atomic_write(output_dir / output_name, text)
        print(output_dir / output_name)


if __name__ == "__main__":
    main()
