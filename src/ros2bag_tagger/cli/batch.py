from pathlib import Path

import typer

from ..mcap_parser import McapParser
from ..utils.bag_info import get_bag_times

app = typer.Typer(
    help="Annotate many bags under a directory",
    invoke_without_command=True,
)


def _process(path: Path) -> None:
    tag_file = path.with_suffix(".json")
    parser = McapParser(path)
    tags = parser.infer_tags()
    start, end = get_bag_times(path)
    tags.time["start_time"] = start
    tags.time["end_time"] = end
    tag_file.write_text(tags.to_json_str(indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(f"  • {path.name} → {tag_file.name}")


@app.callback()
def annotate_directory(
    src_dir: Path = typer.Argument(
        ..., exists=True, file_okay=False, readable=True, help="Directory that contains .mcap files"
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan sub-directories too"),
) -> None:
    """
    Apply tags (defined by *template*) to every bag inside *src_dir*.
    Results are stored next to each bag as `<bag>.tags.json`.
    """

    pattern = "**/*.mcap" if recursive else "*.mcap"
    targets = list(src_dir.glob(pattern))

    if not targets:
        typer.secho("No bag files found - nothing to do.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    typer.echo(f"Tagging {len(targets)} bag(s)…")

    for bag in targets:
        _process(bag)

    typer.secho("Batch annotation finished!", fg=typer.colors.GREEN)
