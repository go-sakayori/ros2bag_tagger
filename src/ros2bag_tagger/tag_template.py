from __future__ import annotations

import json
from importlib.resources import files
from typing import Dict, Tuple

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
    def _empty_for_schema(cls, schema: Dict):
        t = schema.get("type")
        if isinstance(t, list):
            if "object" in t:
                t = "object"
            elif "array" in t:
                t = "array"

        if t == "object":
            props = schema.get("properties", {})
            return {k: cls._empty_for_schema(v) for k, v in props.items()}

        if t == "array":
            return []

        if t == "string":
            return ""

        return None

    @classmethod
    def empty(cls):
        """Return a schema-driven, fully initialized tag container."""
        return cls._empty_for_schema(cls._SCHEMA)

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
