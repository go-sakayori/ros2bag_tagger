"""Command-line interface for ros2bag-tagger.

Sub-commands
------------
* convert   - single MCAP → JSON
* batch     - bulk conversion
* template  - empty tag template
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

from .dataset_tags import DatasetTags
from .mcap_parser import McapParser, McapTaggerError
from .tag_manager import TagManager
from .tag_template import TagTemplate


def _echo_json(ds: DatasetTags) -> None:
    print(ds.to_json_str(indent=2, ensure_ascii=False))


def _save_json(ds: DatasetTags, path: Path) -> None:
    path.write_text(ds.to_json_str(indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {path}")


def _iter_bag_files(inputs: Iterable[str | Path]) -> List[Path]:
    """Yield every *.mcap file found in *inputs*."""
    bags: list[Path] = []
    for input in inputs:
        p = Path(input).expanduser().resolve()
        if p.is_dir():
            bags.extend(p.rglob("*.mcap"))
        elif p.suffix == "*.mcap":
            bags.append(p)
        else:
            print(f"Skipping non-rosbag file: {p}")
    return sorted(bags)


def _cmd_convert(args: argparse.Namespace) -> None:
    try:
        parser = McapParser(args.bag)
        tags = parser.infer_tags()
    except McapTaggerError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run or args.output is None:
        _echo_json(tags)

    if not args.dry_run:
        out_path = (
            Path(args.output).expanduser().resolve()
            if args.output is not None
            else Path(args.bag).with_suffix("_tags.json")
        )
        _save_json(tags, out_path)


def _cmd_batch(args: argparse.Namespace) -> None:
    bag_files = _iter_bag_files(args.input)
    if not bag_files:
        print(f"No ros bag files found.", file=sys.stderr)
        return

    mgr = TagManager()
    for bag in bag_files:
        try:
            tags = McapParser(bag).infer_tags()
            mgr._datasets[bag.stem] = tags
            print(f"processed {bag}")
        except McapTaggerError as exc:
            print(f"{bag} : {exc}", file=sys.stderr)

    mgr.export(args.out_dir)
    print(f"All tag files are written to {args.out_dir}")


def _cmd_template(args: argparse.Namespace) -> None:
    empty = TagTemplate.empty()
    json_str = json.dumps(empty, ensure_ascii=False, indent=2)

    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.write_text(json_str, encoding="utf-8")
        print(f"template written to {path}")
    else:
        print(json_str)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ros2bag-tagger",
        description="Tag your ROS2 bag files and export to JSON.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Convert
    p_convert = sub.add_parser(
        "convert", help="Convert a single ROS2 bag to a tag-JSON file"
    )
    p_convert.add_argument("bag", help="Path to a *.mcap ros bag.")
    p_convert.add_argument(
        "-o", "--output", help="Output file path (default: <bag>_tags.json)."
    )
    p_convert.add_argument(
        "--dry_run", action="store_true", help="Print JSON to stdout instead of saving."
    )
    p_convert.set_defaults(func=_cmd_convert)

    # Batch
    p_batch = sub.add_parser(
        "batch", help="Recursively convert multiple ros bags at once."
    )
    p_batch.add_argument(
        "-i",
        "--input",
        nargs="+",
        help="One or more files/directories to search for *.mcap.",
    )
    p_batch.add_argument(
        "-d",
        "--out_dir",
        required=True,
        help="Directory where all tag-JSON files will be written.",
    )
    p_batch.set_defaults(func=_cmd_batch)

    # Template
    p_template = sub.add_parser("template", help="Output an empty tag‑JSON template.")
    p_template.add_argument(
        "-o", "--output", help="Write template to file instead of stdout."
    )
    p_template.set_defaults(func=_cmd_template)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
