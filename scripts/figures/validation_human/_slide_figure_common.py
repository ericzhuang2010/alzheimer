#!/usr/bin/env python3
"""Shared validation helpers for titleless SEA-AD slide figures."""

from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
from PIL import Image


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "t", "1", "yes"}


def as_int(value: Any, label: str = "value") -> int:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Expected integer {label}, observed {value!r}") from exc
    rounded = int(round(number))
    require(
        math.isfinite(number) and abs(number - rounded) <= 1e-9,
        f"Expected integer {label}, observed {value!r}",
    )
    return rounded


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_strings(values: Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_tsv(path: Path) -> pd.DataFrame:
    require(path.is_file(), f"Missing TSV: {path}")
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, sep="\t", index=False, lineterminator="\n")
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def one_row(frame: pd.DataFrame, label: str) -> pd.Series:
    require(len(frame) == 1, f"Expected one row in {label}, observed {len(frame)}")
    return frame.iloc[0]


def require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    require(not missing, f"Missing columns in {label}: {missing}")


def validate_source_artifact(manifest: pd.DataFrame, relative: str, digest: str) -> None:
    require_columns(
        manifest,
        ["path", "digest_algorithm", "digest_scope", "digest_value"],
        "source artifact manifest",
    )
    rows = manifest.loc[manifest["path"].eq(relative)]
    require(len(rows) == 1, f"Input is not uniquely registered: {relative}")
    row = rows.iloc[0]
    require(row["digest_algorithm"] == "sha256", f"Non-SHA256 registration: {relative}")
    require(row["digest_scope"] == "full_file", f"Non-full-file registration: {relative}")
    require(row["digest_value"] == digest, f"Registered digest mismatch: {relative}")


def check_record(
    schema: str,
    figure_id: str,
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    details: str,
    *,
    severity: str = "blocking",
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": schema,
        "figure_id": figure_id,
        "check_id": check_id,
        "severity": severity,
        "status": status or ("pass" if passed else "fail"),
        "observed": observed,
        "expected": expected,
        "details": details,
    }


def image_checks(
    schema: str,
    figure_id: str,
    image_paths: Sequence[Path],
    *,
    dpi: int,
    width: int,
    height: int,
) -> list[dict[str, Any]]:
    lookup = {path.suffix: path for path in image_paths}
    record = lambda *args, **kwargs: check_record(schema, figure_id, *args, **kwargs)
    nonempty = all(path.stat().st_size > 1000 for path in image_paths)
    checks = [
        record(
            "image_export_set",
            set(lookup) == {".png", ".pdf", ".svg"},
            "|".join(sorted(lookup)),
            ".pdf|.png|.svg",
            "PNG, PDF, and SVG exports are present.",
        ),
        record(
            "image_exports_nonempty",
            nonempty,
            "all >1000" if nonempty else "small file",
            "all >1000",
            "Image exports are nontrivial.",
        ),
    ]
    svg = lookup[".svg"].read_text(encoding="utf-8").lower()
    checks.extend(
        [
            record(
                "svg_searchable_text",
                "<text" in svg,
                "present" if "<text" in svg else "missing",
                "present",
                "SVG text remains searchable.",
            ),
            record(
                "svg_vector_paths",
                "<path" in svg,
                "present" if "<path" in svg else "missing",
                "present",
                "SVG contains vector geometry.",
            ),
            record(
                "pdf_signature",
                lookup[".pdf"].read_bytes()[:5] == b"%PDF-",
                lookup[".pdf"].read_bytes()[:5].decode("latin1"),
                "%PDF-",
                "PDF signature is valid.",
            ),
        ]
    )
    with Image.open(lookup[".png"]) as image:
        observed_width, observed_height = image.size
        embedded = image.info.get("dpi", (math.nan, math.nan))
        mode = image.mode
    checks.extend(
        [
            record(
                "png_dimensions",
                (observed_width, observed_height) == (width, height),
                f"{observed_width}x{observed_height}",
                f"{width}x{height}",
                "PNG dimensions match the frozen slide canvas.",
            ),
            record(
                "png_resolution",
                all(math.isfinite(value) and abs(value - dpi) <= 1 for value in embedded),
                f"{embedded[0]:.2f}|{embedded[1]:.2f}",
                f"{dpi}|{dpi}",
                "Embedded PNG resolution is 450 DPI.",
            ),
            record(
                "png_color_mode",
                mode in {"RGB", "RGBA"},
                mode,
                "RGB or RGBA",
                "PNG uses a slide-compatible color mode.",
            ),
        ]
    )
    return checks


def render_three_formats(
    fig: Any,
    staging: Path,
    figure_id: str,
    *,
    dpi: int,
    title: str,
) -> list[Path]:
    paths: list[Path] = []
    for extension in ("png", "pdf", "svg"):
        final = staging / f"{figure_id}.{extension}"
        temporary = staging / f".{figure_id}.tmp.{os.getpid()}.{extension}"
        if extension == "pdf":
            metadata = {
                "Title": title,
                "Creator": "Validation-human slide-figure renderer",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {
                "Title": title,
                "Creator": "Validation-human slide-figure renderer",
                "Date": None,
            }
        else:
            metadata = {"Software": "Validation-human slide-figure renderer"}
        fig.savefig(
            temporary,
            format=extension,
            dpi=dpi if extension == "png" else None,
            facecolor="#FFFFFF",
            bbox_inches=None,
            pad_inches=0,
            metadata=metadata,
        )
        require(temporary.stat().st_size > 1000, f"Rendered file is too small: {temporary}")
        os.replace(temporary, final)
        paths.append(final)
    return paths


def visible_text_metadata(fig: Any) -> dict[str, Any]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = list(fig.texts)
    for axis in fig.axes:
        texts.extend(axis.texts)
        texts.extend(axis.get_xticklabels())
        texts.extend(axis.get_yticklabels())
        texts.append(axis.xaxis.label)
        texts.append(axis.yaxis.label)
        if axis.title:
            texts.append(axis.title)
    texts = [text for text in texts if text.get_visible() and text.get_text()]
    minimum_font = min((text.get_fontsize() for text in texts), default=math.inf)
    clipped: list[str] = []
    fig_bbox = fig.bbox
    for text in texts:
        bbox = text.get_window_extent(renderer=renderer)
        if (
            bbox.x0 < fig_bbox.x0 - 1
            or bbox.y0 < fig_bbox.y0 - 1
            or bbox.x1 > fig_bbox.x1 + 1
            or bbox.y1 > fig_bbox.y1 + 1
        ):
            clipped.append(text.get_text())
    return {"minimum_font_points": minimum_font, "canvas_clipped_text": clipped}


def table_rows(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA"
    return max(sum(1 for _ in path.open("r", encoding="utf-8")) - 1, 0)


def build_artifacts(
    *,
    schema: str,
    figure_id: str,
    project_root: Path,
    input_digests: Mapping[str, str],
    staging: Path,
    script_paths: Sequence[Path],
    payload_files: Sequence[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for relative, digest in sorted(input_digests.items()):
        path = project_root / relative
        rows.append(
            {
                "schema_version": schema,
                "figure_id": figure_id,
                "artifact_role": "input",
                "logical_name": relative,
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "rows": table_rows(path),
                "validation_state": "validated_frozen_input",
            }
        )
    for script in script_paths:
        relative = str(script.resolve().relative_to(project_root))
        rows.append(
            {
                "schema_version": schema,
                "figure_id": figure_id,
                "artifact_role": "script",
                "logical_name": script.name,
                "path": relative,
                "bytes": script.stat().st_size,
                "sha256": sha256_file(script),
                "rows": "NA",
                "validation_state": "validated_script",
            }
        )
    for name in payload_files:
        path = staging / name
        require(path.is_file() and path.stat().st_size > 0, f"Missing payload: {name}")
        rows.append(
            {
                "schema_version": schema,
                "figure_id": figure_id,
                "artifact_role": "output",
                "logical_name": name,
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "rows": table_rows(path),
                "validation_state": "validated_output",
            }
        )
    frame = pd.DataFrame(rows)
    require(frame["path"].is_unique, "Artifact paths are duplicated")
    require(
        set(frame.loc[frame["artifact_role"].eq("output"), "path"]) == set(payload_files),
        "Artifact output scope changed",
    )
    return frame


def validate_artifacts(
    *,
    project_root: Path,
    output_root: Path,
    artifacts: pd.DataFrame,
    payload_files: Sequence[str],
) -> None:
    require(
        set(artifacts.loc[artifacts["artifact_role"].eq("output"), "path"])
        == set(payload_files),
        "Artifact output scope changed",
    )
    for row in artifacts.itertuples(index=False):
        path = output_root / row.path if row.artifact_role == "output" else project_root / row.path
        require(path.is_file(), f"Missing artifact: {path}")
        require(path.stat().st_size == as_int(row.bytes), f"Artifact byte count changed: {row.path}")
        require(sha256_file(path) == row.sha256, f"Artifact digest changed: {row.path}")
