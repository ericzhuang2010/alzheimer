#!/usr/bin/env python3
"""Shared rendering and publication helpers for Phase 19 slide figures."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


MPL_CACHE = Path(tempfile.gettempdir()) / "phase19_slide_figures_mplconfig"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CACHE)
FONT_CACHE = Path(tempfile.gettempdir()) / "phase19_slide_figures_fontcache"
FONT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["XDG_CACHE_HOME"] = str(FONT_CACHE)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


FIGURE_SIZE = (12.4, 4.7)
PNG_DPI = 450
EXPECTED_PNG_SIZE = (5580, 2115)

# Presentation-safe, colorblind-aware semantic palette.
NAVY = "#17365D"
DARK = "#333333"
MID = "#5B6573"
LIGHT = "#D7DEE8"
PALE = "#F7F9FC"
WHITE = "#FFFFFF"
BLUE = "#0072B2"
PALE_BLUE = "#E9F3F8"
AMBER = "#E69F00"
PALE_AMBER = "#FFF4DD"
VERMILLION = "#D55E00"
PALE_VERMILLION = "#FBEAE4"
GRAY = "#BDBDBD"
PALE_GRAY = "#F1F1F1"
CHARCOAL = "#4D4D4D"
GREEN = "#009E73"


def require(condition: bool, message: str) -> None:
    """Raise a uniform validation error when an invariant is violated."""

    if not condition:
        raise RuntimeError(message)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "t", "1", "yes"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bundle(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((Path(value).resolve() for value in paths), key=str):
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\t")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_tsv(frame: pd.DataFrame, path: Path) -> None:
    require(len(frame) > 0, f"Refusing to write an empty table: {path}")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(
        temporary,
        sep="\t",
        index=False,
        na_rep="NA",
        lineterminator="\n",
    )
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def output_names(stem: str) -> list[str]:
    return [
        f"{stem}.png",
        f"{stem}.pdf",
        f"{stem}.svg",
        f"{stem}_plot_data.tsv",
        f"{stem}_checks.tsv",
        f"{stem}_caption.md",
        f"{stem}_methods.md",
        f"{stem}_artifacts.tsv",
        f"{stem}_status.tsv",
    ]


def apply_presentation_style() -> None:
    """Load the scientific-visualization presentation style, then freeze exports."""

    repository = Path(__file__).resolve().parents[4]
    style = (
        repository
        / ".agents"
        / "skills"
        / "scientific-visualization"
        / "assets"
        / "presentation.mplstyle"
    )
    if style.is_file():
        plt.style.use(style)
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "phase19-genetic-support-slides",
            "hatch.linewidth": 0.7,
            "figure.facecolor": WHITE,
            "figure.constrained_layout.use": False,
            "axes.facecolor": WHITE,
            "savefig.facecolor": WHITE,
            "savefig.bbox": None,
        }
    )


def new_canvas() -> tuple[plt.Figure, plt.Axes]:
    apply_presentation_style()
    figure = plt.figure(figsize=FIGURE_SIZE, facecolor=WHITE)
    axis = figure.add_axes([0, 0, 1, 1])
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    return figure, axis


def rounded_box(
    axis: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    face: str = WHITE,
    edge: str = LIGHT,
    linewidth: float = 1.0,
    radius: float = 0.012,
    hatch: str | None = None,
    zorder: int = 1,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.004,rounding_size={radius}",
        transform=axis.transAxes,
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        hatch=hatch,
        zorder=zorder,
    )
    axis.add_patch(patch)
    return patch


def add_text(
    axis: plt.Axes,
    x: float,
    y: float,
    value: str,
    *,
    size: float = 10.0,
    color: str = DARK,
    weight: str = "normal",
    ha: str = "left",
    va: str = "center",
    linespacing: float = 1.12,
    zorder: int = 5,
) -> None:
    axis.text(
        x,
        y,
        value,
        transform=axis.transAxes,
        fontsize=size,
        color=color,
        fontweight=weight,
        ha=ha,
        va=va,
        linespacing=linespacing,
        family="sans-serif",
        zorder=zorder,
    )


def panel_heading(axis: plt.Axes, letter: str, title: str, x: float, y: float) -> None:
    add_text(axis, x, y, letter, size=13.0, color=NAVY, weight="bold")
    add_text(axis, x + 0.025, y, title, size=12.0, color=NAVY, weight="bold")


def render_triplet(figure: plt.Figure, staging: Path, stem: str) -> None:
    figure.savefig(
        staging / f"{stem}.png",
        dpi=PNG_DPI,
        facecolor=WHITE,
    )
    figure.savefig(
        staging / f"{stem}.pdf",
        facecolor=WHITE,
        metadata={"CreationDate": None, "Creator": "matplotlib"},
    )
    figure.savefig(
        staging / f"{stem}.svg",
        facecolor=WHITE,
        metadata={"Date": None, "Creator": "matplotlib"},
    )
    plt.close(figure)


def make_checks(
    schema: str,
    values: Sequence[tuple[str, Any, Any, str]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for check_id, expected, observed, detail in values:
        passed = str(expected) == str(observed)
        rows.append(
            {
                "schema_version": schema,
                "check_id": check_id,
                "severity": "blocking",
                "status": "pass" if passed else "fail",
                "expected": expected,
                "observed": observed,
                "detail": detail,
            }
        )
    checks = pd.DataFrame(rows)
    failed = checks.loc[checks["status"].ne("pass"), "check_id"].tolist()
    require(not failed, "Figure checks failed: " + ", ".join(failed))
    return checks


def image_checks(staging: Path, stem: str, schema: str) -> pd.DataFrame:
    png = staging / f"{stem}.png"
    pdf = staging / f"{stem}.pdf"
    svg = staging / f"{stem}.svg"
    require(png.is_file(), f"Missing PNG: {png}")
    require(pdf.is_file(), f"Missing PDF: {pdf}")
    require(svg.is_file(), f"Missing SVG: {svg}")
    with Image.open(png) as image:
        dimensions = tuple(image.size)
        dpi = image.info.get("dpi", (0.0, 0.0))
    pdf_header = pdf.read_bytes()[:5]
    svg_text = svg.read_text(encoding="utf-8")
    return make_checks(
        schema,
        [
            (
                "png_dimensions",
                f"{EXPECTED_PNG_SIZE[0]}x{EXPECTED_PNG_SIZE[1]}",
                f"{dimensions[0]}x{dimensions[1]}",
                "Exact slide-native raster dimensions at 450 DPI.",
            ),
            (
                "png_dpi",
                PNG_DPI,
                int(round(float(dpi[0]))),
                "PNG metadata resolution rounded to the requested DPI.",
            ),
            (
                "pdf_signature",
                "%PDF-",
                pdf_header.decode("ascii", errors="replace"),
                "Vector PDF has the expected file signature.",
            ),
            (
                "svg_vector_root",
                "present",
                "present" if "<svg" in svg_text else "absent",
                "SVG contains a vector root element.",
            ),
            (
                "svg_editable_text",
                "present",
                "present" if "<text" in svg_text else "absent",
                "SVG preserves labels as editable text.",
            ),
        ],
    )


def validate_source_status(
    status_path: Path,
    *,
    status_column: str,
    accepted: set[str],
) -> pd.DataFrame:
    require(status_path.is_file(), f"Missing source status: {status_path}")
    frame = pd.read_csv(status_path, sep="\t", low_memory=False)
    require(len(frame) == 1, f"Expected one source-status row: {status_path}")
    require(status_column in frame.columns, f"Missing {status_column}: {status_path}")
    observed = str(frame.iloc[0][status_column])
    require(observed in accepted, f"Unvalidated source status {observed!r}: {status_path}")
    return frame


def validate_blocking_checks(checks_path: Path) -> pd.DataFrame:
    require(checks_path.is_file(), f"Missing source checks: {checks_path}")
    frame = pd.read_csv(checks_path, sep="\t", low_memory=False)
    if "severity" in frame.columns:
        blocking = frame.loc[frame["severity"].astype(str).str.lower().eq("blocking")]
    elif "blocking" in frame.columns:
        blocking = frame.loc[frame["blocking"].map(truth)]
    else:
        # Some validated bundles publish a uniform checks table without an
        # explicit severity flag. In that contract every listed check is
        # required, so validate the complete table.
        blocking = frame
    if "status" in blocking.columns:
        passed = blocking["status"].astype(str).str.lower().eq("pass")
    elif "passed" in blocking.columns:
        passed = blocking["passed"].map(truth)
    else:
        raise RuntimeError(f"Cannot identify check results: {checks_path}")
    require(bool(passed.all()), f"A blocking source check failed: {checks_path}")
    return frame


def publish_package(
    *,
    schema: str,
    stem: str,
    output_root: Path,
    source_paths: Sequence[Path],
    renderer_path: Path,
    plot_data: pd.DataFrame,
    science_checks: pd.DataFrame,
    caption: str,
    methods: str,
    render: Callable[[Path], None],
    status_fields: Mapping[str, Any],
    force: bool,
    visual_review_status: str,
) -> None:
    """Render, validate, and atomically publish one nine-file figure package."""

    require(visual_review_status in {"pending", "complete"}, "Invalid review status")
    names = output_names(stem)
    for path in source_paths:
        require(path.is_file(), f"Missing declared source: {path}")
    require(renderer_path.is_file(), f"Missing renderer: {renderer_path}")
    require(len(plot_data) > 0, "Plot-data table is empty")
    require(len(science_checks) > 0, "Science-check table is empty")
    require(science_checks["status"].eq("pass").all(), "A science check failed")

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{stem}.", dir=output_root.parent))
    try:
        render(staging)
        checks = pd.concat(
            [science_checks, image_checks(staging, stem, schema)],
            ignore_index=True,
        )
        write_tsv(plot_data, staging / names[3])
        write_tsv(checks, staging / names[4])
        write_text(staging / names[5], caption)
        write_text(staging / names[6], methods)

        artifact_rows: list[dict[str, Any]] = []
        for name in names[:7]:
            path = staging / name
            require(path.is_file() and path.stat().st_size > 0, f"Missing artifact: {name}")
            rows: int | str = "NA"
            if path.suffix == ".tsv":
                rows = len(pd.read_csv(path, sep="\t", low_memory=False))
            artifact_rows.append(
                {
                    "schema_version": schema,
                    "path": name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "rows": rows,
                    "validation_state": "validated",
                }
            )
        write_tsv(pd.DataFrame(artifact_rows), staging / names[7])

        source_list = [Path(path).resolve() for path in source_paths]
        status_row: dict[str, Any] = {
            "schema_version": schema,
            "technical_status": "validated_complete",
            "visual_review_status": visual_review_status,
            "output_files": len(names),
            "source_files": len(source_list),
            "source_sha256_bundle": sha256_bundle(source_list),
            "renderer_sha256": sha256_file(renderer_path),
            "figure_width_inches": FIGURE_SIZE[0],
            "figure_height_inches": FIGURE_SIZE[1],
            "png_dpi": PNG_DPI,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
        }
        status_row.update(status_fields)
        write_tsv(pd.DataFrame([status_row]), staging / names[8])

        actual = sorted(path.name for path in staging.iterdir() if path.is_file())
        require(actual == sorted(names), f"Output contract mismatch: {actual}")
        if output_root.exists():
            if not force:
                raise FileExistsError(f"Output exists; use --force to replace: {output_root}")
            backup_root = Path.cwd() / "tmp" / "phase19_genetic_support_figure_backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (
                f"{output_root.name}_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{os.getpid()}"
            )
            output_root.replace(backup)
        staging.replace(output_root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"Published {len(names)} validated figure files to {output_root}")
