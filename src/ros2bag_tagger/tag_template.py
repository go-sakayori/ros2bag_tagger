from __future__ import annotations

import json
from importlib.resources import files
from typing import Dict, List, Tuple

import jsonschema
from jsonschema.validators import validator_for


class TagTemplate:
    """Static container for the fixed set of tag categories."""

    _SCHEMA_PATH = files("ros2bag_tagger.schema").joinpath("tag_schema.json")
    _SCHEMA: Dict = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

    _Validator = validator_for(_SCHEMA)
    _Validator.check_schema(_SCHEMA)
    _VALIDATOR = _Validator(_SCHEMA)

    _LABELS: Tuple[str, ...] = tuple(_SCHEMA["properties"])
    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def category(cls) -> Tuple[str, ...]:
        """Return all categories name as an immutable tuple."""
        return cls._LABELS

    @classmethod
    def subcategory(cls, category: str) -> Tuple[str, ...]:
        """Return the sub-keys defined for *category* (may be empty)."""
        cls._assert_category(category)
        prop_schema = cls._SCHEMA["properties"][category]

        if prop_schema.get("type") == "object":
            return tuple(prop_schema.get("properties", {}).keys())

        items = prop_schema.get("items", {})
        return tuple(items.get("enum", []))

    @classmethod
    def empty(cls) -> Dict[str, Dict[str, List[str]] | List]:
        container: Dict[str, Dict[str, List[str]] | List] = {}
        for cat in cls.category():
            subs = cls.subcategory(cat)
            container[cat] = {sub: [] for sub in subs} if subs else []
        return container

    @classmethod
    def _assert_category(cls, category: str) -> None:
        if category not in cls._LABELS:
            raise KeyError(f"Unknown category: {category}")

    @classmethod
    def validate(cls, category: str) -> None:
        """Raise KeyError if *category* is unknown."""
        cls._assert_category(category)

    @classmethod
    def validate_container(cls, tags: Dict) -> None:
        """
        Validate an entire tag dictionary (output of `empty()` など) against
        the JSON Schema.  Raises jsonschema.ValidationError on failure.
        """
        cls._VALIDATOR.validate(tags)
