import json
import os
from pathlib import Path
from typing import Any, Dict, List

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


def _check_schema(path: Path, data: Any) -> None:
    try:
        TagTemplate.validate_container(data)
    except ValidationError as e:
        typer.secho(
            f"Schema violation\n File: {str(path)}\n Reason: {e.message}", fg=typer.colors.RED
        )
        raise typer.Exit(1)


def _check_semantics(data: dict) -> None:
    errors: List[str] = []

    if any(not isinstance(v, (int, float)) for v in data.get("velocity", [])):
        errors.append("velocity must contain only numbers")

    errors.extend(_validate_ego_vehicle_movement(data))

    if errors:
        for msg in errors:
            typer.secho(f"{msg}", fg=typer.colors.RED)
        raise typer.Exit(1)


def _validate_ego_vehicle_movement(data: Dict[str, Any]) -> List[str]:
    """
    Validates the 'ego_vehicle_movement' section of the tag data.
    Checks that relevant arrays have two numeric items in ascending order.
    """
    validation_errors: List[str] = []

    def _check_array_properties(current_array: List[Any], path: str, errors: List[str]) -> None:
        """Checks if current_array has 2 numbers in ascending order."""
        if len(current_array) != 2:
            errors.append(
                f"Array at path '{path}' must have exactly two items. Found: {len(current_array)}."
            )
            return

        item1, item2 = current_array[0], current_array[1]

        if not all(isinstance(item, (int, float)) for item in current_array):
            errors.append(
                f"Array items at path '{path}' must be numbers. Found: [{item1}, {item2}]."
            )
            return  # Checked in `_check_schema` but double check to avoid raise errors

        if item1 > item2:
            errors.append(
                f"Array items at path '{path}' must be in ascending order. Found: [{item1}, {item2}]."
            )

    ego_movement_data = data.get("ego_vehicle_movement")
    if ego_movement_data is None:
        return validation_errors

    def _traverse_and_validate(current_item: Any, current_path: str) -> None:
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                _traverse_and_validate(value, f"{current_path}.{key}")
        elif isinstance(current_item, list):
            if not current_item:
                return

            first_el = current_item[0]

            # Scenario 1: current_item is a TimeRangeArray (e.g., [[1,2], "string_instead_of_list", [3,4]])
            # Test: first_el is a list AND (it's empty OR its elements are numbers)
            if isinstance(first_el, list) and (
                not first_el or all(isinstance(sub_el, (int, float)) for sub_el in first_el)
            ):
                # first_el is a TimeRange (or an empty list). So, current_item is treated as a TimeRangeArray.
                # Validate each element of current_item as if it should be a TimeRange.
                for i, item_to_check_as_tr in enumerate(current_item):
                    if isinstance(item_to_check_as_tr, list):
                        _check_array_properties(
                            item_to_check_as_tr, f"{current_path}[{i}]", validation_errors
                        )
                    else:
                        # Item in a supposed TimeRangeArray is not a list. This is an error.
                        validation_errors.append(
                            f"Item at path '{current_path}[{i}]' was expected to be a TimeRange (a list) but found type {type(item_to_check_as_tr).__name__}."
                        )

            # Scenario 2: current_item is a list of TimeRangeArrays (e.g., [[[1,2]], [[[3,4],[5,6]]]])
            # Test: first_el is a list AND (it's empty OR its first element is a list)
            # This indicates first_el is itself a TimeRangeArray.
            elif isinstance(first_el, list) and (
                not first_el or (first_el and isinstance(first_el[0], list))
            ):
                # first_el is a TimeRangeArray. So, current_item is a list of TimeRangeArrays.
                # Iterate through current_item; each element (tra_candidate) is a TimeRangeArray.
                for i, tra_candidate in enumerate(current_item):
                    if isinstance(
                        tra_candidate, list
                    ):  # tra_candidate should be a TimeRangeArray (list)
                        # Validate each element (tr_candidate) of tra_candidate as a TimeRange.
                        for j, tr_candidate in enumerate(
                            tra_candidate
                        ):  # tr_candidate should be a TimeRange (list)
                            if isinstance(tr_candidate, list):
                                _check_array_properties(
                                    tr_candidate, f"{current_path}[{i}][{j}]", validation_errors
                                )
                            else:
                                validation_errors.append(
                                    f"Item at path '{current_path}[{i}][{j}]' was expected to be a TimeRange but found type {type(tr_candidate).__name__}."
                                )
                    else:
                        validation_errors.append(
                            f"Item at path '{current_path}[{i}]' was expected to be a TimeRangeArray but found type {type(tra_candidate).__name__}."
                        )

    _traverse_and_validate(ego_movement_data, "ego_vehicle_movement")
    return validation_errors


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
    src: Path = typer.Argument(..., exists=True, readable=True, dir_okay=True),
) -> None:
    """Validate an edited tag-specification JSON."""

    targets = []
    if os.path.isdir(src):
        targets = list(src.glob("*.json"))
    else:
        targets = src

    for file in targets:
        data = _load_json(file)
        _check_schema(file, data)
        _check_semantics(data)

    typer.secho("specification valid", fg=typer.colors.GREEN)
