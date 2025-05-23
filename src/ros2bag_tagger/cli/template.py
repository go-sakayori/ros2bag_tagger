import json
from pathlib import Path

import typer

from ..tag_template import TagTemplate

app = typer.Typer(help="Create and manage tag templates")


@app.command("check")
def new_template(
    output: Path = typer.Option(default=None, help="Output file name (e.g. template.json)"),
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
def validate_template(
    template_file: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """Static validation of a template file."""
    try:
        TagTemplate.load(template_file)
    except ValueError as err:
        typer.secho(f"Invalid template: {err}", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho("Template looks good!", fg=typer.colors.GREEN)
