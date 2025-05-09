from pathlib import Path

import typer

from ..tag_manager import TagManager

app = typer.Typer(
    help="Annotate many bags under a directory",
    invoke_without_command=True,
)


@app.callback()
def annotate_directory(
    src_dir: Path = typer.Argument(
        ..., exists=True, file_okay=False, readable=True, help="Directory that contains .mcap files"
    ),
    template: Path = typer.Option(
        ..., "--template", "-t", exists=True, readable=True, help="Tag template JSON"
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan sub-directories too"),
    workers: int = typer.Option(4, "--jobs", "-j", help="Parallelism"),
) -> None:
    """
    Apply tags (defined by *template*) to every bag inside *src_dir*.
    Results are stored next to each bag as `<bag>.tags.json`.
    """
    tagger = TagManager.from_template(template)

    pattern = "**/*.mcap" if recursive else "*.mcap"
    targets = list(src_dir.glob(pattern))

    if not targets:
        typer.secho("No bag files found - nothing to do.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    typer.echo(f"Tagging {len(targets)} bag(s)…")

    from concurrent.futures import ThreadPoolExecutor

    def _process(path: Path) -> None:
        tag_file = path.with_suffix(".tags.json")
        tags = tagger.generate_tags(path)
        tag_file.write_text(tags.model_dump_json(indent=2))  # or .json(indent=2) for pydantic v1
        typer.echo(f"  • {path.name} → {tag_file.name}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        pool.map(_process, targets)

    typer.secho("Batch annotation finished!", fg=typer.colors.GREEN)
