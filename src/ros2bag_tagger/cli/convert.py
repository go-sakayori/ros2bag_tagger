from pathlib import Path

import typer

from ..mcap_parser import McapParser

app = typer.Typer(
    help="Convert mcap format rosbag files to tagged JSON",
    invoke_without_command=True,
)


@app.callback()
def convert(
    bag: Path = typer.Argument(..., exists=True, readable=True, help="Input .mcap"),
    output: Path = typer.Option(None, "--out", "-o", help="Destination JSON file"),
) -> None:
    """Convert a single bag to JSON with tag information."""
    parser = McapParser(bag)
    tags = parser.infer_tags()
    out_path = output or bag.with_suffix(".json")
    out_path.write_text(tags.to_json_str(indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(f"Wrote {out_path}")
