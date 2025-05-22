import argparse
import sys
from pathlib import Path


def _cmd_map_marker_array(args: argparse.Namespace) -> None:
    src: Path = args.mcap.expanduser().resolve()
    if not src.exists():
        sys.exit(f"Input MCAP not found: {src}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcap-augment", description="Embed map/route blobs into an existing MCAP file."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    map_marker_array = sub.add_parser(
        "map_marker_array", help="Add map marker array into existing MCAP."
    )
    map_marker_array.add_argument("--map", type=Path, required=True, help="Map file path")
    map_marker_array.add_argument("--mcap", type=Path, help="Input MCAP file")
    map_marker_array.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output MCAP (default: <input>_with_maproute.mcap)",
    )
    map_marker_array.set_defaults(func=_cmd_map_marker_array)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
