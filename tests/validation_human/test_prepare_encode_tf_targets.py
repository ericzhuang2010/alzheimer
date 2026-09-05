from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validation_human/11_prepare_encode_tf_targets.py"
SPEC = importlib.util.spec_from_file_location("prepare_encode_tf_targets", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_stored_gzip_is_byte_stable_and_readable(tmp_path: Path) -> None:
    rows = [("ATF3", "ABHD4"), ("CTCF", "MYBPC3")]
    first = tmp_path / "first.tsv.gz"
    second = tmp_path / "second.tsv.gz"
    MODULE.atomic_write_gzip_tsv(first, rows)
    MODULE.atomic_write_gzip_tsv(second, rows)

    assert first.read_bytes() == second.read_bytes()
    with gzip.open(first, "rt", encoding="utf-8") as handle:
        assert handle.read().splitlines() == [
            "parent\tchild\tsource\trelease",
            "ATF3\tABHD4\tENCODE\tENCODE_2012_Gerstein_filtered_proximal_TIP",
            "CTCF\tMYBPC3\tENCODE\tENCODE_2012_Gerstein_filtered_proximal_TIP",
        ]


def test_cli_maps_current_and_previous_symbols_and_rejects_bad_edges(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "TF1 proximal_filtered TARGET\n"
        "TF1 proximal_filtered OLD\n"
        "TF1 proximal_filtered MISSING\n"
        "TF1 proximal_filtered TF1\n",
        encoding="utf-8",
    )
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()

    gencode = tmp_path / "gencode.gtf.gz"
    with gzip.open(gencode, "wt", encoding="utf-8") as handle:
        for index, (stable, symbol) in enumerate(
            (("ENSG000001", "TF1"), ("ENSG000002", "TARGET"), ("ENSG000003", "NEW")),
            start=1,
        ):
            handle.write(
                f'chr1\ttest\tgene\t{index}\t{index}\t.\t+\t.\t'
                f'gene_id "{stable}.1"; gene_type "protein_coding"; '
                f'gene_name "{symbol}";\n'
            )

    hgnc = tmp_path / "hgnc.tsv"
    columns = [
        "symbol",
        "status",
        "alias_symbol",
        "prev_symbol",
        "ensembl_gene_id",
    ]
    with hgnc.open("wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {
                    "symbol": "TF1",
                    "status": "Approved",
                    "alias_symbol": "",
                    "prev_symbol": "",
                    "ensembl_gene_id": "ENSG000001",
                },
                {
                    "symbol": "TARGET",
                    "status": "Approved",
                    "alias_symbol": "",
                    "prev_symbol": "",
                    "ensembl_gene_id": "ENSG000002",
                },
                {
                    "symbol": "NEW",
                    "status": "Approved",
                    "alias_symbol": "",
                    "prev_symbol": "OLD",
                    "ensembl_gene_id": "ENSG000003",
                },
            ]
        )

    output = tmp_path / "output.tsv.gz"
    summary = tmp_path / "summary.tsv"
    rejections = tmp_path / "rejections.tsv"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source",
            str(source),
            "--source-sha256",
            source_sha256,
            "--gencode",
            str(gencode),
            "--hgnc",
            str(hgnc),
            "--output",
            str(output),
            "--summary",
            str(summary),
            "--rejections",
            str(rejections),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "final_edges=2" in result.stdout

    with gzip.open(output, "rt", encoding="utf-8", newline="") as handle:
        output_rows = list(csv.DictReader(handle, delimiter="\t"))
    assert [(row["parent"], row["child"]) for row in output_rows] == [
        ("TF1", "NEW"),
        ("TF1", "TARGET"),
    ]

    rejection_rows = list(csv.DictReader(rejections.open(), delimiter="\t"))
    assert {row["reason"] for row in rejection_rows} == {
        "self_loop",
        "unresolved_child",
    }
