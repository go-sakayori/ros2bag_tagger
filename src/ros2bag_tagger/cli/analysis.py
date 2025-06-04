import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import typer
import yaml

app = typer.Typer(help="Analyze json files under a directory", invoke_without_command=True)


def insert_totals(d: dict) -> Tuple[dict, float]:
    total = 0.0
    keys_to_delete = []
    for k, v in d.items():
        if k == "__self":
            total += v
            keys_to_delete.append(k)
        elif isinstance(v, dict):
            d[k], subtotal = insert_totals(v)
            total += subtotal
        else:
            total += v
    for k in keys_to_delete:
        del d[k]
    d["total"] = total
    return d, total


def apply_percent(d: dict, grand_total: float) -> dict:
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = apply_percent(v, grand_total)
        elif k == "total":
            result[k] = f"{round(v, 3)} ({round(v / grand_total * 100, 2)}%)"
        else:
            result[k] = f"{round(v, 3)} ({round(v / grand_total * 100, 2)}%)"
    return result


def _format_nested_durations(flat: dict) -> dict:
    tree = {}
    for key, val in flat.items():
        parts = key.split("/")

        if len(parts) == 1:
            tree.setdefault(parts[0], {})
            tree[parts[0]]["__self"] = tree[parts[0]].get("__self", 0.0) + val
        elif len(parts) == 2:
            tree.setdefault(parts[0], {})
            tree[parts[0]].setdefault(parts[1], 0.0)
            tree[parts[0]][parts[1]] += val
        elif len(parts) == 3:
            tree.setdefault(parts[0], {})
            tree[parts[0]].setdefault(parts[1], {})
            tree[parts[0]][parts[1]].setdefault(parts[2], 0.0)
            tree[parts[0]][parts[1]][parts[2]] += val

    tree, grand_total = insert_totals(tree)
    tree["total"] = grand_total
    return apply_percent(tree, grand_total)


def _safe_duration(intervals):
    total = 0.0
    for interval in intervals:
        if isinstance(interval, list) and len(interval) == 2:
            start, end = interval
            total += end - start
    return total


def _flatten_movement_structure(evm: dict, prefix=""):
    flat_durations = {}
    for key, value in evm.items():
        full_key = f"{prefix}/{key}" if prefix else key
        if isinstance(value, list):
            dur = _safe_duration(value)
            flat_durations[full_key] = dur
        elif isinstance(value, dict):
            flat_durations.update(_flatten_movement_structure(value, prefix=full_key))
    return flat_durations


def _process(path: Path) -> Tuple[float, Dict[str, float]]:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise typer.Exit(0)

    movement_duration = {}

    with file_path.open() as f:
        data = json.load(f)
        ego_movement = data.get("ego_vehicle_movement", {})
        durations = _flatten_movement_structure(ego_movement)

        for category, dur in durations.items():
            movement_duration[category] = movement_duration.get(category, 0.0) + dur

    return movement_duration


def _to_dict(d):
    if isinstance(d, defaultdict):
        return {k: _to_dict(v) for k, v in d.items()}
    return d


@app.callback()
def analyze_directory(
    src_dir: Path = typer.Argument(
        ..., exists=True, file_okay=False, readable=True, help="Directory that contains .json files"
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan sub-directories too."),
) -> None:
    pattern = "**/*.json" if recursive else "*.json"
    targets = list(src_dir.glob(pattern))

    if not targets:
        typer.secho("No json files found - nothing to do.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    typer.echo(f"Analyzing {len(targets)} json(s)…")

    merged_movements = defaultdict(float)

    for json_file in targets:
        movement = _process(json_file)
        for k, v in movement.items():
            merged_movements[k] += v

    formatted = _format_nested_durations(merged_movements)
    typer.echo(yaml.dump(_to_dict(formatted), allow_unicode=True, sort_keys=False))
