from pathlib import Path

import typer

from ..mcap_parser import McapParser

app = typer.Typer(
    help="Convert mcap format rosbag files to tagged JSON", invoke_without_command=True
)


@app.callback()
def bag_to_json(
    bag: Path = typer.Argument(..., exists=True, readable=True, help="Input .mcap"),
    output: Path = typer.Option(None, "--out", "-o", help="Destination JSON file"),
) -> None:
    """Convert a single bag to JSON with tag information."""
    parser = McapParser(bag)
    data = parser.to_dict()
    if output is None:
        output = bag.with_suffix(".json")
    output.write_text(parser.dumps(data))
    typer.echo(f"Wrote {output}")
