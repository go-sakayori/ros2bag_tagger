"""MCAP parser module.

Parse MCAP file and infer without any ROS runtime dependency.
The implementation relies solely on the PyPIpackage mcap.
"""

from __future__ import annotations

from pathlib import Path

from mcap.reader import make_reader
from mcap.records import Message, Schema

from .dataset_tags import DatasetTags


class McapTaggerError(RuntimeError):
    """Raised when parsing fails or the file is unreadable."""


class McapParser:
    """Infer :class:DatasetTags from a slice of an MCAP recording."""

    def __init__(self, mcap_path: str | Path) -> None:
        """Instantiate a parser for *mcap_path*.

        Parameters
        ----------
        mcap_path
        """
        self.path = Path(mcap_path).expanduser().resolve()
        if not self.path.exists():
            raise McapTaggerError(f"File not found: {self.path}")

    def infer_tags(self) -> DatasetTags:
        """
        Very naive tag inference.

        *Replace this logic.*
        """
        ds = DatasetTags()

        with self.path.open("rb") as fh:
            reader = make_reader(fh)
            start_time: float | None = None

            for msg in reader.iter_messages():
                msg_time_sec = msg.log_time / 1e9  # nanosec -> sec

                # record first timestamp
                if start_time is None:
                    start_time = msg_time_sec

                # stop after 60 sec window
                if msg_time_sec - start_time > self.SLICE_SEC:
                    break

                self._apply_rules(msg, ds, reader.schemas)

        # fallback defaults (optional)
        if not ds.to_dict()["weather"]:
            ds.set("weather", ["unknown"])

        return ds

    def _apply_rules(self, msg: Message, ds: DatasetTags, schemas: dict[int, Schema]) -> None:
        """Inspect each message and mutate DatasetTags in‑place."""
        topic = msg.channel.topic

        # simplistic traffic volume heuristic
        if "/object" in topic:
            ds.set("traffic_volume", ["heavy_traffic"])

        # time of day from frame_id (dummy rule)
        if b"night" in msg.data:
            ds.set("time_of_day", ["night"])

        # schema‑based weather hint
        schema_name = schemas[msg.channel.schema_id].name.lower()
        if "weather" in schema_name:
            ds.set("weather", ["rainy"])
