from typing import Iterable

from .tag_template import TagTemplate


class DatasetTags:
    def __init__(self) -> None:
        self._tags: dict[str, list[str]] = TagTemplate.empty()

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
