import json
import os
from pathlib import Path
from typing import Any, List

import typer
from jsonschema import ValidationError

from ..tag_template import TagTemplate

app = typer.Typer(help="Create and manage json files with tags")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        typer.secho(f"JSON parse error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


def _check_schema(data: Any) -> None:
    try:
        TagTemplate.validate_container(data)
    except ValidationError as e:
        typer.secho(f"Schema violation: {e.message}", fg=typer.colors.RED)
        raise typer.Exit(1)


def _check_semantics(data: dict) -> None:
    errors: List[str] = []

    if any(not isinstance(v, (int, float)) for v in data.get("velocity", [])):
        errors.append("velocity must contain only numbers")

    if errors:
        for msg in errors:
            typer.secho(f"{msg}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("create")
def init_template(
    output: Path = typer.Option(
        None, "--output", "-o", help="Output file name (e.g. template.json)"
    ),
) -> None:
    """
    Create a new tag template JSON.
    """
    template = TagTemplate.empty()
    if output is None:
        print(f"{json.dumps(template, indent=2, ensure_ascii=False)}")
        return
    output.write_text(json.dumps(template, indent=2, ensure_ascii=False))
    typer.echo(f"Template saved to {output}")


@app.command("validate")
def validate_file(
    src: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    """Validate an edited tag-specification JSON."""

    targets = []
    if os.path.isdir(src):
        targets = list(src.glob("*.json"))
    else:
        targets = src

    for file in targets:
        data = _load_json(file)
        _check_schema(data)
        _check_semantics(data)

    typer.secho("specification valid", fg=typer.colors.GREEN)
