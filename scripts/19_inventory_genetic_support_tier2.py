#!/usr/bin/env python3
"""Inventory registered Phase 19 Tier 2 Synapse containers without downloading."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import synapseclient
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/phase19_genetic_support_tier2.yml",
        help="Tier 2 scientific configuration",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Inventory directory; defaults below the configured external root",
    )
    parser.add_argument("--max-entities", type=int, default=100_000)
    return parser.parse_args()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def atomic_write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "inventory_utc",
        "dataset_id",
        "source_root_id",
        "entity_id",
        "parent_id",
        "depth",
        "name",
        "entity_type",
        "version_number",
        "version_label",
        "data_file_handle_id",
        "content_size",
        "content_md5",
        "concrete_type",
        "role",
        "access_state",
        "access_error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)
        temporary = Path(handle.name)
    temporary.replace(path)


def lower_type(value: Any) -> str:
    return str(value or "").lower()


def may_have_children(entity_type: Any) -> bool:
    value = lower_type(entity_type)
    return any(key in value for key in ("folder", "project", "dataset"))


def is_file(entity_type: Any) -> bool:
    value = lower_type(entity_type)
    return value == "file" or value.endswith(".fileentity")


def entity_properties(entity: Any) -> dict[str, Any]:
    if entity is None:
        return {}
    if isinstance(entity, dict):
        return dict(entity)
    try:
        return dict(entity)
    except (TypeError, ValueError):
        return dict(getattr(entity, "properties", {}) or {})


def inventory_source(
    syn: synapseclient.Synapse,
    item: dict[str, Any],
    inventory_utc: str,
    max_entities: int,
) -> list[dict[str, Any]]:
    source_id = str(item["source_id"])
    dataset_id = str(item["dataset_id"])
    role = str(item["role"])
    rows: list[dict[str, Any]] = []
    queue: list[tuple[str, int, str | None]] = [(source_id, 0, None)]
    visited: set[str] = set()

    while queue:
        entity_id, depth, parent_hint = queue.pop(0)
        if entity_id in visited:
            continue
        if len(visited) >= max_entities:
            raise RuntimeError(
                f"Inventory exceeded --max-entities={max_entities} for {source_id}"
            )
        visited.add(entity_id)
        row: dict[str, Any] = {
            "inventory_utc": inventory_utc,
            "dataset_id": dataset_id,
            "source_root_id": source_id,
            "entity_id": entity_id,
            "parent_id": parent_hint,
            "depth": depth,
            "role": role,
            "access_state": "metadata_accessible",
            "access_error": None,
        }

        try:
            entity = syn.get(entity_id, downloadFile=False)
            props = entity_properties(entity)
            row.update(
                {
                    "parent_id": props.get("parentId", parent_hint),
                    "name": props.get("name"),
                    "entity_type": props.get("concreteType"),
                    "version_number": props.get("versionNumber"),
                    "version_label": props.get("versionLabel"),
                    "data_file_handle_id": props.get("dataFileHandleId"),
                    "concrete_type": props.get("concreteType"),
                }
            )
            handle_id = props.get("dataFileHandleId")
            if handle_id:
                try:
                    handle = syn.restGET(f"/fileHandle/{handle_id}")
                    row["content_size"] = handle.get("contentSize")
                    row["content_md5"] = handle.get("contentMd5")
                except Exception as error:
                    row["access_state"] = "entity_accessible_file_handle_unavailable"
                    row["access_error"] = f"{type(error).__name__}: {error}"
        except Exception as error:
            row["access_state"] = "metadata_denied"
            row["access_error"] = f"{type(error).__name__}: {error}"
            rows.append(row)
            continue

        rows.append(row)
        if depth == 0 or may_have_children(row.get("entity_type")):
            try:
                for child in syn.getChildren(entity_id):
                    child_id = str(child["id"])
                    child_type = child.get("type")
                    if child_id not in visited:
                        queue.append((child_id, depth + 1, entity_id))
                    if not may_have_children(child_type) and not is_file(child_type):
                        continue
            except Exception as error:
                row["access_state"] = "entity_accessible_children_denied"
                row["access_error"] = f"{type(error).__name__}: {error}"

    return rows


def main() -> int:
    args = parse_args()
    root = Path.cwd().resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = root / output_dir
    else:
        output_dir = root / config["inputs"]["external_root"] / "inventory"

    token = os.environ.pop("SYNAPSE_AUTH_TOKEN", None)
    if token is None and not Path("~/.synapseConfig").expanduser().exists():
        token = getpass.getpass("Synapse personal access token: ")

    syn = synapseclient.Synapse(silent=True)
    if token:
        syn.login(authToken=token)
    else:
        syn.login()
    token = None

    profile = syn.getUserProfile()
    inventory_utc = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for item in config["synapse_sources"]:
        rows.extend(inventory_source(syn, item, inventory_utc, args.max_entities))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tsv_path = output_dir / f"synapse_tier2_inventory_{stamp}.tsv"
    json_path = output_dir / f"synapse_tier2_inventory_{stamp}.json"
    atomic_write_tsv(tsv_path, rows)
    manifest = {
        "schema_version": "phase19_tier2_synapse_inventory_v1",
        "inventory_utc": inventory_utc,
        "authenticated_owner_id": profile.get("ownerId"),
        "authenticated_username": profile.get("userName"),
        "source_count": len(config["synapse_sources"]),
        "entity_count": len(rows),
        "metadata_accessible": sum(
            row["access_state"] != "metadata_denied" for row in rows
        ),
        "metadata_denied": sum(
            row["access_state"] == "metadata_denied" for row in rows
        ),
        "tsv_path": str(tsv_path.relative_to(root)),
    }
    atomic_write_text(json_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        f"Authenticated Synapse user {manifest['authenticated_username']}; "
        f"inventoried {manifest['entity_count']} entities from "
        f"{manifest['source_count']} registered sources."
    )
    print(f"Inventory TSV: {tsv_path}")
    print(f"Inventory manifest: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
