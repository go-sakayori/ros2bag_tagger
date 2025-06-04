import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import typer
import yaml

app = typer.Typer(help="Analyze json files under a directory", invoke_without_command=True)


def _format_nested_durations(flat: dict) -> dict:
    def nested_dict():
        return defaultdict(nested_dict_or_float)

    def nested_dict_or_float():
        return defaultdict(float)

    tree = defaultdict(nested_dict)

    for key, val in flat.items():
        parts = key.split("/")
        if len(parts) == 1:
            tree[parts[0]] = round(val, 3)
        elif len(parts) == 2:
            if not isinstance(tree[parts[0]], dict):
                tree[parts[0]] = defaultdict(float)
            if isinstance(tree[parts[0]][parts[1]], dict):
                continue
            tree[parts[0]][parts[1]] += val
        elif len(parts) == 3:
            if not isinstance(tree[parts[0]], dict):
                tree[parts[0]] = defaultdict(lambda: defaultdict(float))
            if not isinstance(tree[parts[0]][parts[1]], dict):
                tree[parts[0]][parts[1]] = defaultdict(float)
            tree[parts[0]][parts[1]][parts[2]] += val

    for cat, sub in tree.items():
        if isinstance(sub, dict):
            for subcat, subval in sub.items():
                if isinstance(subval, dict):
                    sub[subcat]["total"] = round(sum(subval.values()), 3)
            try:
                tree[cat]["total"] = round(
                    sum(
                        sub[subcat]["total"]
                        if isinstance(sub[subcat], dict) and "total" in sub[subcat]
                        else sub[subcat]
                        for subcat in sub
                    ),
                    3,
                )
            except Exception:
                pass

    return tree


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
            # flat_durations[full_key] = _safe_duration(value)
            dur = _safe_duration(value)
            if dur > 0:
                print(f"[DEBUG] {full_key}: {dur}")
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
        start, end = data["time"]
        total_log_time = end - start
        ego_movement = data.get("ego_vehicle_movement", {})
        durations = _flatten_movement_structure(ego_movement)

        for category, dur in durations.items():
            movement_duration[category] = movement_duration.get(category, 0.0) + dur

    return total_log_time, movement_duration


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

    total_log_time = 0.0
    merged_movements = defaultdict(float)

    for json_file in targets:
        log_time, movement = _process(json_file)
        total_log_time += log_time
        for k, v in movement.items():
            merged_movements[k] += v

    typer.echo(f"Total log time: {round(total_log_time, 3)} sec\n")
    formatted = _format_nested_durations(merged_movements)
    typer.echo(yaml.dump(_to_dict(formatted), allow_unicode=True, sort_keys=False))
