from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict

from .dataset_tags import DatasetTags
from .utils.bag_info import get_bag_times


class TagManager:
    def __init__(self, template: dict | None = None) -> None:
        self._datasets: Dict[str, DatasetTags] = {}
        self._template = deepcopy(template) if template else None

    @classmethod
    def from_template(cls, path: str | Path) -> "TagManager":
        """Load a template JSON and return a pre-seeded TagManager."""
        with Path(path).expanduser().open(encoding="utf-8") as fh:
            data = json.load(fh)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, mapping: dict) -> "TagManager":
        mgr = cls()
        ds = mgr.new_dataset("template")
        ds.load_from_dict(deepcopy(mapping))
        return mgr

    def generate_tags(self, bag_path: str | Path) -> DatasetTags:
        path = Path(bag_path)
        ds = self.new_dataset(path.stem)

        start, end = get_bag_times(path)
        ds.meta = {
            "start_time": start,
            "end_time": end,
        }

        if self._template:
            ds._tags = deepcopy(self._template)
        else:
            ds._tags = deepcopy(DatasetTags()._tags)

        return ds

    def new_dataset(self, name: str) -> DatasetTags:
        if name in self._datasets:
            raise KeyError(f"Dataset '{name}' already exists.")
        self._datasets[name] = DatasetTags()
        return self._datasets[name]

    def get(self, name: str) -> DatasetTags:
        return self._datasets[name]

    def remove(self, name: str) -> None:
        self._datasets.pop(name, None)

    def export(self, output_dir: str | Path) -> None:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)

        for name, tags in self._datasets.items():
            out.joinpath(f"{name}.json").write_text(
                tags.to_json_str(indent=2, ensure_ascii=False), encoding="utf-8"
            )

    def keys(self):
        """Return all dataset names managed by this instance."""
        return self._datasets.keys()

    def values(self):
        """Return all DatasetTags objects."""
        return self._datasets.values()

    def items(self):
        """Return (name, DatasetTags) pairs."""
        return self._datasets.items()

    def __len__(self) -> int:  # pragma: no cover
        return len(self._datasets)

    def __contains__(self, name: str) -> bool:  # pragma: no cover
        return name in self._datasets
