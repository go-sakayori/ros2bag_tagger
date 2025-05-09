from typing import Iterable

from .tag_template import TagTemplate


class DatasetTags:
    def __init__(self) -> None:
        self._tags: dict[str, list[str]] = TagTemplate.empty()
        self._tags["dynamic_object"] = {
            "vehicle": [],
            "two_wheeler": [],
            "pedestrian": [],
            "unknown": [],
        }
        self._tags["ego_vehicle_movement"] = {
            "lane keep": [],
            "left turn": [],
            "right turn": [],
            "lane change": [],
            "obstacle avoidance": [],
            "stopped": [],
            "parked": [],
            "pull out": [],
            "pull over": [],
        }

    def set(self, category: str, values: Iterable[str]) -> "DatasetTags":
        TagTemplate.validate(category)
        self._tags[category] = list(values)
        return self

    def add(self, category: str, *values: str) -> "DatasetTags":
        TagTemplate.validate(category)
        current = set(self._tags[category])
        current.update(values)
        self._tags[category] = sorted(current)
        return self

    def add_dynamic_object(self, group: str, *values: str) -> None:
        """Add items to dynamic_object[group]."""
        current = set(self._tags["dynamic_object"][group])
        current.update(values)
        self._tags["dynamic_object"][group] = sorted(current)

    def remove(self, category: str, *values: str) -> "DatasetTags":
        TagTemplate.validate(category)
        current = set(self._tags[category])
        current.difference_update(values)
        self._tags[category] = sorted(current)
        return self

    def to_dict(self) -> dict[str, list[str]]:
        """Return a shallow copy of the internal dict."""
        return {k: list(v) for k, v in self._tags.items()}

    def to_json_str(self, *, ensure_ascii: bool = False, indent: int = 2) -> str:
        """Serialize tags to a JSON string."""
        import json

        return json.dumps(self._tags, ensure_ascii=ensure_ascii, indent=indent)
