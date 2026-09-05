#!/usr/bin/env python3
"""Import the frozen SEA-AD GDA-8 VCF through the audited D1-to-D2 map."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import mmap
import os
import re
import tarfile
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO

import yaml


DNA = frozenset("ACGT")
PALINDROMIC = {frozenset(("A", "T")), frozenset(("C", "G"))}
COMPLEMENT = str.maketrans("ACGT", "TGCA")
SNP_PATTERN = re.compile(r"^\[([ACGT])/([ACGT])\]$")
PLINK_CHROMOSOMES = {"23": "X", "24": "Y", "25": "XY", "26": "MT"}
PAR1_END = 2_781_479
PAR2_START = 155_701_383
PAR2_END = 156_040_895

AUDIT_METRICS = (
    "classification_invalid_d2_location",
    "classification_missing_d2_marker",
    "classification_palindromic_snv_excluded",
    "classification_provisional_reference_aligned",
    "classification_source_not_biallelic_snv",
    "classification_xy_outside_grch38_par",
    "coordinate_source_matches_d1_normalized",
    "d1_d2_refstrand_changed_accepted",
    "d1_d2_refstrand_identical_accepted",
    "d1_source_name_matches",
    "d2_assay_rows_scanned",
    "d2_source_name_matches",
    "duplicate_grch38_variant_keys",
    "final_duplicate_target_records_excluded",
    "final_unique_reference_aligned",
    "genotype_index_swapped",
    "genotype_index_unchanged",
    "plink_chromosome_23_to_X_matches_d1",
    "plink_chromosome_24_to_Y_matches_d1",
    "plink_chromosome_25_to_XY_matches_d1",
    "plink_chromosome_26_to_MT_matches_d1",
    "records_at_duplicate_grch38_variant_keys",
    "source_duplicate_ids",
    "source_eligible_ids",
    "source_rejected_rows",
    "source_to_d1_orientation_direct",
    "source_to_d1_orientation_reverse_complement",
    "source_variant_rows",
    "xy_candidates_merged_to_x",
    "xy_merged_to_x_reference_aligned",
)


@dataclass(frozen=True)
class SourceMarker:
    raw_chromosome: str
    chromosome: str
    position: int
    ref: str
    alt: str


@dataclass(frozen=True)
class ManifestMarker:
    chromosome: str | None
    position: int | None
    genome_build: str
    snp: str
    ilmn_strand: str
    ref_strand: str


@dataclass(frozen=True)
class Transform:
    chromosome: str
    position: int
    ref: str
    alt: str
    orientation: str
    swap: bool
    source: SourceMarker
    d1_ref_strand: str
    d2_ref_strand: str


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configured_path(project_root: Path, value: object) -> Path:
    path = Path(str(value))
    return (path if path.is_absolute() else project_root / path).resolve()


def normalize_chromosome(value: object) -> str | None:
    chromosome = clean(value)
    if chromosome.lower().startswith("chr"):
        chromosome = chromosome[3:]
    chromosome = chromosome.upper()
    if chromosome == "M":
        chromosome = "MT"
    chromosome = PLINK_CHROMOSOMES.get(chromosome, chromosome)
    if chromosome in {"X", "Y", "XY", "MT"}:
        return chromosome
    try:
        number = int(chromosome)
    except ValueError:
        return None
    return str(number) if 1 <= number <= 22 else None


def positive_integer(value: object) -> int | None:
    try:
        number = int(clean(value))
    except ValueError:
        return None
    return number if number > 0 else None


def parse_snp(value: object) -> tuple[str, str] | None:
    match = SNP_PATTERN.fullmatch(clean(value).upper())
    return None if match is None else (match.group(1), match.group(2))


def reverse_complement(base: str) -> str:
    return base.translate(COMPLEMENT)


def is_missing_vcf(value: str) -> bool:
    return value in {"", "."}


def read_audit_metrics(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    observed: dict[str, int] = {}
    for row in rows:
        metric = clean(row.get("metric"))
        value = clean(row.get("value"))
        if metric:
            try:
                observed[metric] = int(value)
            except ValueError as exc:
                raise RuntimeError(
                    f"Noninteger frozen audit value for {metric}: {value!r}"
                ) from exc
    missing = sorted(set(AUDIT_METRICS) - set(observed))
    if missing:
        raise RuntimeError(f"Frozen final audit is missing metrics: {missing}")
    return observed


def read_source(
    archive: Path, member: str
) -> tuple[dict[str, SourceMarker], list[str], Counter[str]]:
    markers: dict[str, SourceMarker] = {}
    samples: list[str] = []
    metrics: Counter[str] = Counter()
    with tarfile.open(archive, "r:gz") as container:
        raw_handle = container.extractfile(member)
        if raw_handle is None:
            raise RuntimeError(f"VCF member is unavailable: {member}")
        for raw in raw_handle:
            if raw.startswith(b"##"):
                continue
            line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
            if line.startswith("#CHROM"):
                fields = line.split("\t")
                samples = fields[9:]
                continue
            if line.startswith("#") or not line:
                continue
            fields = line.split("\t", 9)
            metrics["source_variant_rows"] += 1
            if len(fields) < 5:
                continue
            raw_chromosome = clean(fields[0])
            chromosome = normalize_chromosome(raw_chromosome)
            position = positive_integer(fields[1])
            marker_id = clean(fields[2])
            ref = clean(fields[3]).upper()
            alt = clean(fields[4]).upper()
            eligible = (
                chromosome is not None
                and position is not None
                and not is_missing_vcf(marker_id)
                and not is_missing_vcf(ref)
                and not is_missing_vcf(alt)
            )
            if not eligible:
                continue
            metrics["source_eligible_ids"] += 1
            normalized_raw = raw_chromosome.upper().removeprefix("CHR")
            if normalized_raw in PLINK_CHROMOSOMES:
                metrics[
                    f"plink_chromosome_{normalized_raw}_to_"
                    f"{PLINK_CHROMOSOMES[normalized_raw]}_matches_d1"
                ] += 1
            if marker_id in markers:
                metrics["source_duplicate_ids"] += 1
                continue
            markers[marker_id] = SourceMarker(
                raw_chromosome=raw_chromosome,
                chromosome=chromosome,
                position=position,
                ref=ref,
                alt=alt,
            )
    metrics["source_rejected_rows"] = (
        metrics["source_variant_rows"] - metrics["source_eligible_ids"]
    )
    if not samples:
        raise RuntimeError("The source VCF has no #CHROM sample header")
    return markers, samples, metrics


def assay_rows(zip_path: Path, member: str) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as raw:
            handle = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            for line in handle:
                if line.strip() == "[Assay]":
                    break
            else:
                raise RuntimeError(f"{member} has no [Assay] section")
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise RuntimeError(f"{member} has no assay header")
            for row in reader:
                first = clean(next(iter(row.values()), ""))
                if first.startswith("[") and first.endswith("]"):
                    break
                yield row


def read_manifest(
    zip_path: Path, member: str, wanted: set[str]
) -> tuple[dict[str, ManifestMarker], int]:
    matches: dict[str, ManifestMarker] = {}
    scanned = 0
    for row in assay_rows(zip_path, member):
        scanned += 1
        name = clean(row.get("Name"))
        if name not in wanted:
            continue
        if name in matches:
            raise RuntimeError(f"Duplicate relevant manifest Name: {name}")
        matches[name] = ManifestMarker(
            chromosome=normalize_chromosome(row.get("Chr")),
            position=positive_integer(row.get("MapInfo")),
            genome_build=clean(row.get("GenomeBuild")),
            snp=clean(row.get("SNP")).upper(),
            ilmn_strand=clean(row.get("IlmnStrand")).upper(),
            ref_strand=clean(row.get("RefStrand")),
        )
    return matches, scanned


class IndexedFasta:
    def __init__(self, fasta_path: Path, fai_path: Path):
        self.handle = fasta_path.open("rb")
        self.mapping = mmap.mmap(self.handle.fileno(), 0, access=mmap.ACCESS_READ)
        self.index: dict[str, tuple[int, int, int, int]] = {}
        self.order: list[str] = []
        with fai_path.open(encoding="utf-8") as handle:
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 5:
                    raise RuntimeError(f"Malformed FAI row: {line!r}")
                name = fields[0]
                self.order.append(name)
                self.index[name] = tuple(map(int, fields[1:5]))

    def close(self) -> None:
        self.mapping.close()
        self.handle.close()

    def base(self, chromosome: str, position: int) -> str | None:
        contig = "chrM" if chromosome == "MT" else f"chr{chromosome}"
        entry = self.index.get(contig)
        if entry is None:
            return None
        length, offset, line_bases, line_bytes = entry
        if not 1 <= position <= length:
            return None
        zero_based = position - 1
        byte_offset = (
            offset
            + (zero_based // line_bases) * line_bytes
            + (zero_based % line_bases)
        )
        return chr(self.mapping[byte_offset]).upper()

    def canonical_contigs(self) -> list[tuple[str, int]]:
        names = [str(value) for value in range(1, 23)] + ["X", "Y", "MT"]
        result: list[tuple[str, int]] = []
        for name in names:
            fai_name = "chrM" if name == "MT" else f"chr{name}"
            if fai_name in self.index:
                result.append((name, self.index[fai_name][0]))
        return result


def is_biallelic_snv(source: SourceMarker) -> bool:
    return (
        len(source.ref) == 1
        and len(source.alt) == 1
        and source.ref in DNA
        and source.alt in DNA
        and source.ref != source.alt
    )


def target_chromosome(marker: ManifestMarker) -> tuple[str | None, bool]:
    chromosome = marker.chromosome
    if marker.genome_build != "38" or chromosome is None or marker.position is None:
        return None, False
    if chromosome != "XY":
        return chromosome, False
    position = marker.position
    in_par = position <= PAR1_END or PAR2_START <= position <= PAR2_END
    return ("X" if in_par else None), True


def allele_transform(
    source: SourceMarker,
    d1: ManifestMarker,
    d2: ManifestMarker,
    target_chrom: str,
    reference_base: str,
) -> tuple[str, str, str, bool]:
    d1_snp = parse_snp(d1.snp)
    d2_snp = parse_snp(d2.snp)
    if d1_snp is None or d2_snp is None:
        raise RuntimeError("A biallelic source SNV has an invalid manifest SNP field")
    if d1_snp != d2_snp or d1.ilmn_strand != d2.ilmn_strand:
        raise RuntimeError("D1/D2 A/B or IlmnStrand identity changed")
    source_set = {source.ref, source.alt}
    design_set = set(d1_snp)
    if source_set == design_set:
        orientation = "direct"
        source_ref_design = source.ref
    elif {reverse_complement(value) for value in source_set} == design_set:
        orientation = "reverse_complement"
        source_ref_design = reverse_complement(source.ref)
    else:
        raise RuntimeError("Source alleles cannot be resolved against D1 A/B identity")

    if source_ref_design == d1_snp[0]:
        source_ref_index = 0
    elif source_ref_design == d1_snp[1]:
        source_ref_index = 1
    else:
        raise RuntimeError("Source REF cannot be assigned to a D1 A/B index")

    if d2.ref_strand == "+":
        genomic = d2_snp
    elif d2.ref_strand == "-":
        genomic = tuple(reverse_complement(value) for value in d2_snp)
    else:
        raise RuntimeError(f"Invalid D2 RefStrand: {d2.ref_strand!r}")

    if reference_base == genomic[0]:
        target_ref_index = 0
    elif reference_base == genomic[1]:
        target_ref_index = 1
    else:
        raise RuntimeError(
            f"GRCh38 reference does not match D2 alleles at "
            f"{target_chrom}:{d2.position}"
        )
    return (
        genomic[target_ref_index],
        genomic[1 - target_ref_index],
        orientation,
        source_ref_index != target_ref_index,
    )


def build_transforms(
    source: dict[str, SourceMarker],
    d1_records: dict[str, ManifestMarker],
    d2_records: dict[str, ManifestMarker],
    fasta: IndexedFasta,
    metrics: Counter[str],
) -> dict[str, Transform]:
    provisional: dict[str, Transform] = {}
    for marker_id, source_marker in source.items():
        d1 = d1_records.get(marker_id)
        if d1 is None:
            raise RuntimeError(f"Eligible source marker is absent from D1: {marker_id}")
        if (
            d1.chromosome != source_marker.chromosome
            or d1.position != source_marker.position
        ):
            raise RuntimeError(
                f"Source/D1 normalized coordinate mismatch for {marker_id}"
            )
        metrics["coordinate_source_matches_d1_normalized"] += 1

        d2 = d2_records.get(marker_id)
        if d2 is None:
            metrics["classification_missing_d2_marker"] += 1
            continue

        # Preserve the frozen audit's mutually exclusive rejection precedence:
        # an invalid ordinary D2/GRCh38 location is classified before the
        # source-allele filters. XY remains a valid D2 chromosome here; its
        # GRCh38 PAR gate is applied after the allele filters below.
        chromosome, was_xy = target_chromosome(d2)
        if not was_xy and chromosome is None:
            metrics["classification_invalid_d2_location"] += 1
            continue
        if not is_biallelic_snv(source_marker):
            metrics["classification_source_not_biallelic_snv"] += 1
            continue
        if frozenset((source_marker.ref, source_marker.alt)) in PALINDROMIC:
            metrics["classification_palindromic_snv_excluded"] += 1
            continue

        if was_xy:
            if chromosome is None:
                metrics["classification_xy_outside_grch38_par"] += 1
                continue
            metrics["xy_candidates_merged_to_x"] += 1
        if d2.position is None:
            raise AssertionError("A valid target must have a position")
        reference_base = fasta.base(chromosome, d2.position)
        if reference_base is None:
            raise RuntimeError(
                f"GRCh38 contig/position is absent for {marker_id}: "
                f"{chromosome}:{d2.position}"
            )
        ref, alt, orientation, swap = allele_transform(
            source_marker, d1, d2, chromosome, reference_base
        )
        transform = Transform(
            chromosome=chromosome,
            position=d2.position,
            ref=ref,
            alt=alt,
            orientation=orientation,
            swap=swap,
            source=source_marker,
            d1_ref_strand=d1.ref_strand,
            d2_ref_strand=d2.ref_strand,
        )
        provisional[marker_id] = transform
        metrics["classification_provisional_reference_aligned"] += 1
        metrics[f"source_to_d1_orientation_{orientation}"] += 1
        metrics[
            "genotype_index_swapped" if swap else "genotype_index_unchanged"
        ] += 1
        metrics[
            "d1_d2_refstrand_identical_accepted"
            if d1.ref_strand == d2.ref_strand
            else "d1_d2_refstrand_changed_accepted"
        ] += 1
        if was_xy:
            metrics["xy_merged_to_x_reference_aligned"] += 1

    key_counts = Counter(
        (item.chromosome, item.position, item.ref, item.alt)
        for item in provisional.values()
    )
    duplicate_keys = {key for key, count in key_counts.items() if count > 1}
    duplicate_records = sum(key_counts[key] for key in duplicate_keys)
    metrics["duplicate_grch38_variant_keys"] = len(duplicate_keys)
    metrics["records_at_duplicate_grch38_variant_keys"] = duplicate_records
    metrics["final_duplicate_target_records_excluded"] = duplicate_records
    final = {
        marker_id: item
        for marker_id, item in provisional.items()
        if (item.chromosome, item.position, item.ref, item.alt)
        not in duplicate_keys
    }
    metrics["final_unique_reference_aligned"] = len(final)
    return final


def atomic_tsv(path: Path, header: list[str], rows: Iterator[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def atomic_gzip_text(path: Path) -> tuple[TextIO, Path, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    raw = os.fdopen(fd, "wb")
    compressed = gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0
    )
    text_handle = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    return text_handle, Path(temporary_name), raw


def publish_gzip(
    path: Path, writer_function
) -> None:
    handle, temporary_path, raw = atomic_gzip_text(path)
    try:
        writer_function(handle)
        handle.flush()
        handle.detach().close()
        raw.flush()
        os.fsync(raw.fileno())
        raw.close()
        os.replace(temporary_path, path)
    finally:
        try:
            handle.close()
        except Exception:
            pass
        try:
            raw.close()
        except Exception:
            pass
        if temporary_path.exists():
            temporary_path.unlink()


def write_mapping(path: Path, transforms: dict[str, Transform]) -> None:
    header = [
        "source_marker_id",
        "source_chromosome",
        "source_position",
        "source_ref",
        "source_alt",
        "target_chromosome",
        "target_position",
        "target_ref",
        "target_alt",
        "source_to_d1_orientation",
        "swap_genotype_indices",
        "d1_refstrand",
        "d2_refstrand",
    ]

    def write(handle: TextIO) -> None:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        for marker_id in sorted(
            transforms,
            key=lambda value: (
                chromosome_sort_key(transforms[value].chromosome),
                transforms[value].position,
                value,
            ),
        ):
            item = transforms[marker_id]
            writer.writerow(
                [
                    marker_id,
                    item.source.raw_chromosome,
                    item.source.position,
                    item.source.ref,
                    item.source.alt,
                    item.chromosome,
                    item.position,
                    item.ref,
                    item.alt,
                    item.orientation,
                    int(item.swap),
                    item.d1_ref_strand,
                    item.d2_ref_strand,
                ]
            )

    publish_gzip(path, write)


def chromosome_sort_key(chromosome: str) -> int:
    if chromosome.isdigit():
        return int(chromosome)
    return {"X": 23, "Y": 24, "MT": 25}[chromosome]


def swap_genotype(sample_field: str, format_field: str) -> str:
    keys = format_field.split(":")
    try:
        gt_index = keys.index("GT")
    except ValueError as exc:
        raise RuntimeError("Source VCF FORMAT lacks GT") from exc
    values = sample_field.split(":")
    if gt_index >= len(values):
        raise RuntimeError("Source VCF sample field lacks the declared GT value")
    parts = re.split(r"([/|])", values[gt_index])
    for index in range(0, len(parts), 2):
        if parts[index] == "0":
            parts[index] = "1"
        elif parts[index] == "1":
            parts[index] = "0"
        elif parts[index] != ".":
            raise RuntimeError(f"Unexpected allele index in biallelic GT: {parts[index]}")
    values[gt_index] = "".join(parts)
    return ":".join(values)


def write_vcf(
    path: Path,
    archive: Path,
    member: str,
    transforms: dict[str, Transform],
    expected_samples: list[str],
    contigs: list[tuple[str, int]],
) -> None:
    written = 0

    def write(output: TextIO) -> None:
        nonlocal written
        injected = False
        with tarfile.open(archive, "r:gz") as container:
            raw_handle = container.extractfile(member)
            if raw_handle is None:
                raise RuntimeError(f"VCF member is unavailable: {member}")
            for raw in raw_handle:
                line = raw.decode("utf-8", errors="strict").rstrip("\r\n")
                if line.startswith("##contig=") or line.startswith("##reference="):
                    continue
                if line.startswith("##"):
                    output.write(line + "\n")
                    continue
                if line.startswith("#CHROM"):
                    fields = line.split("\t")
                    if fields[9:] != expected_samples:
                        raise RuntimeError("Source VCF sample header changed between passes")
                    output.write("##reference=GENCODE_v44_GRCh38_primary_assembly\n")
                    output.write(
                        "##seaad_rimbanet_transform="
                        "GDA8_D1_AB_to_D2_RefStrand_GRCh38_FASTA\n"
                    )
                    for chromosome, length in contigs:
                        output.write(
                            f"##contig=<ID={chromosome},length={length}>\n"
                        )
                    output.write(line + "\n")
                    injected = True
                    continue
                if line.startswith("#") or not line:
                    continue
                fields = line.split("\t")
                if len(fields) < 10:
                    raise RuntimeError("Source VCF data row has fewer than ten fields")
                item = transforms.get(fields[2])
                if item is None:
                    continue
                fields[0] = item.chromosome
                fields[1] = str(item.position)
                fields[3] = item.ref
                fields[4] = item.alt
                fields[7] = "."
                if item.swap:
                    fields[9:] = [
                        swap_genotype(value, fields[8]) for value in fields[9:]
                    ]
                output.write("\t".join(fields) + "\n")
                written += 1
        if not injected:
            raise RuntimeError("Source VCF #CHROM header was not written")

    publish_gzip(path, write)
    if written != len(transforms):
        path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Normalized VCF wrote {written} variants; expected {len(transforms)}"
        )


def verify_audit(
    expected: dict[str, int], observed: Counter[str], output: Path
) -> None:
    atomic_tsv(
        output,
        ["metric", "value"],
        ([metric, int(observed[metric])] for metric in AUDIT_METRICS),
    )
    differences = [
        f"{metric}: observed={observed[metric]} expected={expected[metric]}"
        for metric in AUDIT_METRICS
        if int(observed[metric]) != expected[metric]
    ]
    if differences:
        raise RuntimeError(
            "Production mapping does not reproduce the frozen final audit:\n"
            + "\n".join(differences)
        )


def verify_frozen_inputs(
    paths: dict[str, Path], expected_identity: dict[str, object]
) -> None:
    contracts = {
        "source": (
            "genotype_source_sha256",
            "genotype_source_bytes",
        ),
        "d1": ("genotype_d1_manifest_sha256", None),
        "d2": ("genotype_d2_manifest_sha256", None),
        "reference": ("genotype_reference_sha256", None),
        "fai": ("genotype_reference_fai_sha256", None),
        "audit": ("genotype_final_audit_sha256", None),
    }
    for name, (sha_key, bytes_key) in contracts.items():
        path = paths[name]
        if not path.is_file():
            raise RuntimeError(f"Missing frozen {name} input: {path}")
        if bytes_key and path.stat().st_size != int(expected_identity[bytes_key]):
            raise RuntimeError(f"Frozen {name} byte count changed: {path}")
        observed = sha256_file(path)
        expected = str(expected_identity[sha_key])
        if observed != expected:
            raise RuntimeError(
                f"Frozen {name} SHA-256 changed: observed={observed} expected={expected}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    project_root_value = Path(str(config.get("project_root", ".")))
    project_root = (
        project_root_value
        if project_root_value.is_absolute()
        else Path.cwd() / project_root_value
    ).resolve()
    inputs = config["inputs"]
    identity = config["expected_identity"]
    paths = {
        "source": configured_path(project_root, inputs["genotype_source_archive"]),
        "d1": configured_path(project_root, inputs["genotype_d1_manifest"]),
        "d2": configured_path(project_root, inputs["genotype_d2_manifest"]),
        "reference": configured_path(
            project_root, inputs["genotype_reference_fasta"]
        ),
        "fai": configured_path(project_root, inputs["genotype_reference_fai"]),
        "audit": configured_path(project_root, inputs["genotype_final_audit"]),
    }
    verify_frozen_inputs(paths, identity)
    frozen_audit = read_audit_metrics(paths["audit"])

    print("Reading eligible source markers...", flush=True)
    source, samples, metrics = read_source(
        paths["source"], str(inputs["genotype_source_member"])
    )
    if len(samples) != int(identity["genotype_source_samples"]):
        raise RuntimeError(
            f"Source sample count is {len(samples)}, expected "
            f"{identity['genotype_source_samples']}"
        )
    if len(set(samples)) != len(samples):
        raise RuntimeError("Source VCF sample IDs are not unique")
    if len(source) != int(identity["genotype_eligible_markers"]):
        raise RuntimeError(
            f"Eligible source marker count is {len(source)}, expected "
            f"{identity['genotype_eligible_markers']}"
        )

    wanted = set(source)
    print("Reading matching D1 manifest records...", flush=True)
    d1_records, _ = read_manifest(paths["d1"], "GDA-8v1-0_D1.csv", wanted)
    metrics["d1_source_name_matches"] = len(d1_records)
    print("Reading matching D2 manifest records...", flush=True)
    d2_records, d2_scanned = read_manifest(
        paths["d2"], "GDA-8v1-0_D2.csv", wanted
    )
    metrics["d2_assay_rows_scanned"] = d2_scanned
    metrics["d2_source_name_matches"] = len(d2_records)
    if len(d1_records) != len(source):
        raise RuntimeError(
            f"D1 matched {len(d1_records)} of {len(source)} eligible source markers"
        )

    print("Reproducing the frozen allele audit...", flush=True)
    fasta = IndexedFasta(paths["reference"], paths["fai"])
    try:
        transforms = build_transforms(
            source, d1_records, d2_records, fasta, metrics
        )
        raw_prefix = configured_path(
            project_root, inputs["genotype_raw_plink_prefix"]
        )
        observed_summary = Path(f"{raw_prefix}.import_summary.tsv")
        verify_audit(frozen_audit, metrics, observed_summary)

        mapping_path = Path(f"{raw_prefix}.variant_mapping.tsv.gz")
        vcf_path = Path(f"{raw_prefix}.vcf.gz")
        print("Writing the frozen variant mapping...", flush=True)
        write_mapping(mapping_path, transforms)
        print("Writing the normalized controlled VCF...", flush=True)
        write_vcf(
            vcf_path,
            paths["source"],
            str(inputs["genotype_source_member"]),
            transforms,
            samples,
            fasta.canonical_contigs(),
        )
    finally:
        fasta.close()

    status_path = Path(f"{raw_prefix}.import_status.tsv")
    atomic_tsv(
        status_path,
        [
            "schema_version",
            "stage",
            "state",
            "samples",
            "variants",
            "config_sha256",
            "final_audit_sha256",
        ],
        iter(
            [[
                "seaad_gda8_import_status_v1",
                "VH11C_IMPORT",
                "validated_complete",
                len(samples),
                len(transforms),
                sha256_file(config_path),
                sha256_file(paths["audit"]),
            ]]
        ),
    )
    artifact_path = Path(f"{raw_prefix}.import_artifacts.tsv")
    artifacts = [observed_summary, mapping_path, vcf_path, status_path]
    atomic_tsv(
        artifact_path,
        ["path", "bytes", "sha256"],
        (
            [str(path), path.stat().st_size, sha256_file(path)]
            for path in artifacts
        ),
    )
    print(
        f"VH11C import validated: samples={len(samples)} "
        f"variants={len(transforms)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
