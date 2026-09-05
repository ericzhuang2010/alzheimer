from __future__ import annotations

import importlib.util
import io
import tarfile
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "scripts/validation_human"
FIXTURE = ROOT / "tests/fixtures/seaad_rimbanet"
sys.path.insert(0, str(SCRIPT_DIR))
import rimbanet_common


def load_script(name: str):
    path = SCRIPT_DIR / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prepare = load_script("11_prepare_rimbanet_inputs.py")
priors = load_script("11_build_rimbanet_priors.py")
audit = load_script("11_audit_rimbanet_inputs.py")
submit = load_script("11_submit_rimbanet_minerva.py")


def test_discretized_contract_and_xml():
    nodes, matrix, samples = prepare.read_discretized(
        FIXTURE / "data.discretized.txt"
    )
    assert nodes == ["GENE_A", "GENE_B", "GENE_C", "GENE_D"]
    assert samples == 6
    assert set(matrix[0]) == {0, 1, 2}
    xml = prepare.node_xml(nodes, "Microglia")
    assert '<NETWORK size="4">' in xml
    assert xml.count("<VARIABLE>") == 4
    assert "<VALUE>down</VALUE>" in xml


def test_identity_banned_matrix(tmp_path):
    path = tmp_path / "banned.txt"
    prepare.write_identity(4, path)
    rows = [line.split() for line in path.read_text().splitlines()]
    assert len(rows) == 4
    assert all(len(row) == 4 for row in rows)
    assert rows[0] == ["1", "0", "0", "0"]
    assert rows[3] == ["0", "0", "0", "1"]


def test_fake_runtime_generates_expression_base_prior(tmp_path):
    data = tmp_path / "data.discretized.txt"
    data.write_bytes((FIXTURE / "data.discretized.txt").read_bytes())
    node_path = tmp_path / "node.xml"
    node_path.write_text(prepare.node_xml(["GENE_A", "GENE_B", "GENE_C", "GENE_D"], "Microglia"))
    fake = FIXTURE / "fake_testBN.py"
    fake.chmod(0o755)
    output = tmp_path / "prior.base.txt"
    prepare.generate_base_prior(fake, node_path, data, 6, output)
    base = priors.parse_base_prior(output)
    assert len(base) == 12
    assert {row["parent"] for row in base} == {"GENE_A", "GENE_B", "GENE_C", "GENE_D"}


def test_prior_parser_and_direction_conflict():
    base = priors.parse_base_prior(FIXTURE / "prior.base.txt")
    assert len(base) == 6
    evidence = pd.DataFrame(
        [
            {"parent": "GENE_A", "child": "GENE_B", "source": "CIT", "added_weight": 2.0},
            {"parent": "GENE_B", "child": "GENE_A", "source": "ENCODE", "added_weight": 2.0},
            {"parent": "GENE_A", "child": "GENE_C", "source": "CIT", "added_weight": 3.0},
        ]
    )
    selected, conflicts = priors.resolve_conflicts(evidence)
    selected_edges = set(zip(selected["parent"], selected["child"]))
    assert ("GENE_A", "GENE_B") in selected_edges
    assert ("GENE_B", "GENE_A") not in selected_edges
    assert ("GENE_A", "GENE_C") in selected_edges
    assert len(conflicts) == 1


def test_plink_file_detection(tmp_path):
    prefix = tmp_path / "cohort"
    for suffix in [".pgen", ".pvar", ".psam"]:
        prefix.with_suffix(suffix).write_text("x")
    assert [path.suffix for path in audit.plink_files(prefix)] == [
        ".pgen",
        ".pvar",
        ".psam",
    ]


def test_array_vcf_header_and_final_summary_readers(tmp_path):
    archive_path = tmp_path / "source.tar.gz"
    member = "SEA_AD_SNPs_vcf/sea_ad.vcf"
    payload = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t1_H1\t2_H2\n"
        "1\t10\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\n"
    ).encode()
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo(member)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    assert audit.read_vcf_samples(archive_path, member) == ["1_H1", "2_H2"]

    summary_path = tmp_path / "summary.tsv"
    summary_path.write_text("metric\tvalue\nsource_variant_rows\t3\n")
    assert audit.summary_metrics(summary_path) == {"source_variant_rows": 3}



def test_minerva_bsub_command_uses_execution_profile(tmp_path):
    command = submit.build_bsub_command(
        project_root=tmp_path,
        config_path=tmp_path / "config.yml",
        image_path=tmp_path / "rimbanet.sif",
        storage_root=tmp_path / "scratch",
        log_root=tmp_path / "scratch/logs",
        network="Microglia",
        lsf={
            "task_start": 1,
            "task_end": 1000,
            "array_concurrency": 25,
            "cores_per_task": 1,
            "memory_mb_per_task": 32000,
            "walltime": "12:00",
            "queue": "premium",
        },
        project="acc_test",
    )
    assert command[:3] == ["bsub", "-P", "acc_test"]
    assert "seaad_Microglia[1-1000]%25" in command
    assert "rusage[mem=32000]" in command
    environment = command[command.index("-env") + 1]
    assert f"PROJECT_ROOT={tmp_path}" in environment
    assert "NETWORK=Microglia" in environment
    assert f"RIMBANET_STORAGE_ROOT={tmp_path / 'scratch'}" in environment
    assert str(tmp_path / "scratch/logs/Microglia/%J.%I.out") in command


def test_rimbanet_config_routes_generated_outputs_outside_repo(tmp_path):
    scratch_output = tmp_path.parent / f"{tmp_path.name}_scratch/results/validation_human"
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "seaad_rimbanet_config_v1",
                "project_root": str(tmp_path),
                "output_root": "results/validation_human",
                "phase_directory": "11_seaad_rimbanet",
                "storage": {"generated_output_root": str(scratch_output)},
            }
        )
    )
    _, _, project_root, output_root = rimbanet_common.load_rimbanet_config(
        config_path
    )
    assert project_root == tmp_path
    assert output_root == scratch_output
    assert rimbanet_common.provenance_path(output_root, project_root) == str(
        scratch_output
    )


def test_production_bulk_paths_are_under_minerva_scratch():
    scientific = yaml.safe_load((ROOT / "config/seaad_rimbanet.yml").read_text())
    execution = yaml.safe_load(
        (ROOT / "config/seaad_rimbanet_execution.yml").read_text()
    )
    scratch = Path("/sc/arion/scratch/zhuane01/alzheimer")
    scratch_paths = [
        scientific["storage"]["generated_output_root"],
        scientific["method"]["external_checkout"],
        scientific["method"]["binary"],
        scientific["inputs"]["pseudobulk_directory"],
        scientific["inputs"]["genotype_d1_manifest"],
        scientific["inputs"]["genotype_d2_manifest"],
        scientific["inputs"]["genotype_reference_fasta"],
        scientific["inputs"]["genotype_reference_fai"],
        scientific["inputs"]["genotype_final_audit"],
        scientific["inputs"]["genotype_raw_plink_prefix"],
        scientific["inputs"]["genotype_plink_prefix"],
        scientific["inputs"]["encode_tf_targets"],
        scientific["genetics"]["genotype_matrix"],
        scientific["genetics"]["variant_positions"],
        scientific["genetics"]["ancestry_covariates"],
        execution["runtime"]["image"],
        execution["paths"]["generated_output_root"],
        execution["paths"]["scratch_root"],
        execution["paths"]["log_root"],
        execution["paths"]["external_rimbanet"],
    ]
    controlled_source = Path(
        "/sc/arion/projects/adineto/sea_ad/Data/SNP_Genomic_Variants/"
        "SEA_AD_SNPs_vcf.tar.gz"
    )
    assert Path(scientific["storage"]["root"]) == scratch
    assert Path(execution["paths"]["storage_root"]) == scratch
    assert all(Path(value).is_relative_to(scratch) for value in scratch_paths)
    assert Path(scientific["inputs"]["genotype_source_archive"]) == controlled_source
    assert execution["lsf_production"]["project"] == "acc_adineto"
    assert not Path(scientific["release_root"]).is_absolute()
    assert not Path(
        scientific["inputs"]["genotype_sample_crosswalk"]
    ).is_absolute()


def test_minerva_scaleout_requires_completed_pilot(tmp_path):
    scratch_output = tmp_path / "scratch/results/validation_human"
    scientific = {
        "cohort": {"pilot_network": "Microglia"},
        "output_root": "results/validation_human",
        "phase_directory": "11_seaad_rimbanet",
        "storage": {"generated_output_root": str(scratch_output)},
    }
    try:
        submit.require_pilot_gate(tmp_path, scientific, "Astrocytes")
    except RuntimeError as exc:
        assert "Pilot gate is missing" in str(exc)
    else:
        raise AssertionError("Scale-out should require the Microglia pilot gate")

    status = (
        scratch_output
        / "11_seaad_rimbanet"
        / "11h_release_qc/Microglia/status.tsv"
    )
    status.parent.mkdir(parents=True)
    status.write_text("state\nvalidated_complete\n")
    gate = status.parents[2] / "11f_runs/pilot_gate.tsv"
    gate.parent.mkdir(parents=True)
    gate.write_text("state\npassed\n")
    submit.require_pilot_gate(tmp_path, scientific, "Astrocytes")


def test_scheduler_neutral_task_and_resume(tmp_path):
    output_root = (
        tmp_path.parent / f"{tmp_path.name}_scratch/results/validation_human"
    )
    input_dir = (
        output_root
        / "11_seaad_rimbanet/11e_inputs/Microglia"
    )
    input_dir.mkdir(parents=True)
    (input_dir / "data.discretized.txt").write_bytes(
        (FIXTURE / "data.discretized.txt").read_bytes()
    )
    (input_dir / "node.xml").write_text(
        prepare.node_xml(["GENE_A", "GENE_B", "GENE_C", "GENE_D"], "Microglia")
    )
    (input_dir / "prior.txt").write_bytes((FIXTURE / "prior.base.txt").read_bytes())
    prepare.write_identity(4, input_dir / "banned.txt")
    (input_dir / "bn.param.txt").write_text(
        "\n".join(
            [
                "6",
                "4",
                "node.xml",
                "data.discretized.txt",
                "banned.txt",
                "prior.txt",
                "Microglia",
                "3",
                "networks",
                "result",
            ]
        )
        + "\n"
    )
    (input_dir / "sample_manifest.tsv").write_bytes(
        (FIXTURE / "sample_manifest.tsv").read_bytes()
    )
    pd.DataFrame(
        {
            "source_symbol": ["GENE_A", "GENE_B", "GENE_C", "GENE_D"],
            "final_node_order": [0, 1, 2, 3],
        }
    ).to_csv(input_dir / "gene_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        {
            "node_order": [0, 1, 2, 3],
            "source_symbol": ["GENE_A", "GENE_B", "GENE_C", "GENE_D"],
        }
    ).to_csv(input_dir / "nodes.tsv", sep="\t", index=False)
    prior_dir = output_root / "11_seaad_rimbanet/11d_priors/Microglia"
    prior_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"network": "Microglia", "selected_prior_directions": 2}]
    ).to_csv(prior_dir / "prior_summary.tsv", sep="\t", index=False)
    config = {
        "schema_version": "seaad_rimbanet_config_v1",
        "project_root": ".",
        "output_root": "results/validation_human",
        "storage": {"generated_output_root": str(output_root)},
        "phase_directory": "11_seaad_rimbanet",
        "networks": ["Microglia"],
        "method": {
            "name": "RIMBANet",
            "mode": "full_integrative",
            "source_commit": "fixture",
            "external_checkout": "external_tools/BayesianNetwork",
        },
        "release_id": "fixture_release",
        "release_root": "data/bayesian_network/SEAAD_fixture",
        "release_checks": {"maximum_indegree": 3},
        "cohort": {
            "pilot_network": "Microglia",
            "require_pilot_before_scaleout": True,
        },
        "consensus": {
            "denominator": 3,
            "minimum_direction_support": 0.15,
            "minimum_adjacency_support": 0.30,
        },
        "rimbanet": {
            "number_of_searches": 3,
            "base_seed": 1237,
            "trylist_maximum": 5000000,
            "mutual_information_cutoff": -1,
            "eqtl_threshold": 0,
            "prior_scaling": 1,
            "qratio_offset": 1000,
            "alpha_base": 0.65,
            "alpha_sample_step": 0.015,
            "alpha_sample_divisor": 100,
            "output_prefix": "result",
        },
    }
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config))
    fake = FIXTURE / "fake_testBN.py"
    fake.chmod(0o755)
    command = [
        "bash",
        str(SCRIPT_DIR / "11_run_rimbanet_task.sh"),
        "--config",
        str(config_path),
        "--network",
        "Microglia",
        "--task-id",
        "1",
        "--binary",
        str(fake),
    ]
    first = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    for task_id in (2, 3):
        task_command = command.copy()
        task_command[task_command.index("1")] = str(task_id)
        result = subprocess.run(
            task_command, cwd=tmp_path, text=True, capture_output=True
        )
        assert result.returncode == 0, result.stderr
    second = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    assert "already validated" in second.stdout
    run_dir = output_root / "11_seaad_rimbanet/11f_runs/Microglia"
    status = pd.read_csv(run_dir / "task.1.status.tsv", sep="\t")
    assert status.loc[0, "state"] == "validated_complete"
    assert status.loc[0, "seed"] == 1238

    validate = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "11_validate_rimbanet_runs.py"),
            "--config",
            str(config_path),
            "--network",
            "Microglia",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert validate.returncode == 0, validate.stderr

    counter_dir = tmp_path / "external_tools/BayesianNetwork/script"
    counter_dir.mkdir(parents=True)
    shutil.copy(
        ROOT / "external_tools/BayesianNetwork/script/countDirectLinksMatrix.pl",
        counter_dir / "countDirectLinksMatrix.pl",
    )
    consensus = subprocess.run(
        [
            "bash",
            str(SCRIPT_DIR / "11_build_rimbanet_consensus.sh"),
            "--config",
            str(config_path),
            "--network",
            "Microglia",
            "--binary",
            str(fake),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert consensus.returncode == 0, consensus.stderr
    final_path = (
        output_root
        / "11_seaad_rimbanet/11g_consensus/Microglia/result.links3.links.txt"
    )
    assert final_path.exists()
    assert "GENE_A\tGENE_B" in final_path.read_text()

    publish = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "11_validate_publish_seaad_networks.py"),
            "--config",
            str(config_path),
            "--network",
            "Microglia",
            "--binary",
            str(fake),
            "--consensus-script",
            str(SCRIPT_DIR / "11_build_rimbanet_consensus.sh"),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert publish.returncode == 0, publish.stderr
    release = tmp_path / "data/bayesian_network/SEAAD_fixture/Microglia"
    assert (release / "result.links3.links.txt").exists()
    assert (release / "edge_support.tsv.gz").exists()
    assert (release / "network_manifest.yml").exists()
